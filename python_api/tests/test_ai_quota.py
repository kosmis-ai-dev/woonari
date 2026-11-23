"""CR-013 / T-027: hard daily limits across requests, restarts and processes."""

from __future__ import annotations

import json
import os
import sqlite3
import stat
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.ai_quota import DailyAIQuota
from app.errors import DomainError


class Clock:
    def __init__(self, instant=datetime(2026, 11, 19, 6, tzinfo=UTC)):
        self.instant = instant

    def __call__(self):
        return self.instant


@pytest.fixture
def state(tmp_path):
    private = tmp_path.resolve() / "private"
    return private, private / "ai/usage.sqlite3", Clock()


def quota(state, **kwargs):
    private, path, clock = state
    return DailyAIQuota(path, private_root=private, clock=clock, **kwargs)


def expect_error(code, action, status=503):
    with pytest.raises(DomainError) as caught:
        action()
    assert caught.value.code == code
    assert caught.value.status == status
    assert "private" not in caught.value.message


def test_usage_is_aggregate_only_reading_does_not_consume_and_files_are_private(state):
    value = quota(state)
    expected = {
        "limit": 100, "used": 0, "remaining": 100, "date": "2026-11-19",
        "timezone": "Asia/Seoul", "reset_at": "2026-11-20T00:00:00+09:00",
    }
    assert value.status() == value.status() == expected
    assert value.reserve() == {**expected, "used": 1, "remaining": 99}
    private, path, _ = state
    assert stat.S_IMODE(private.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(value.lock_path.stat().st_mode) == 0o600


def test_the_hundredth_reservation_succeeds_and_101st_is_rejected_across_restarts(state):
    first, other = quota(state), quota(state)
    for index in range(100):
        assert (first if index % 2 else other).reserve()["used"] == index + 1
    expect_error("ai_daily_limit_reached", quota(state).reserve, 429)
    assert quota(state).status()["used"] == 100
    assert quota(state).status()["remaining"] == 0


def test_failed_upstream_attempt_is_not_refunded(state):
    value = quota(state, limit=2)
    try:
        value.reserve()
        raise TimeoutError("upstream failed after reservation")
    except TimeoutError:
        pass
    assert quota(state, limit=2).reserve()["used"] == 2
    expect_error("ai_daily_limit_reached", value.reserve, 429)


def test_korean_midnight_resets_new_day_without_erasing_previous_counts(state):
    private, path, clock = state
    clock.instant = datetime(2026, 11, 19, 14, 59, 59, tzinfo=UTC)
    value = quota(state, limit=1)
    assert value.reserve()["date"] == "2026-11-19"
    expect_error("ai_daily_limit_reached", value.reserve, 429)
    clock.instant = datetime(2026, 11, 19, 15, tzinfo=UTC)
    assert quota(state, limit=1).status() == {
        "limit": 1, "used": 0, "remaining": 1, "date": "2026-11-20",
        "timezone": "Asia/Seoul", "reset_at": "2026-11-21T00:00:00+09:00",
    }
    assert DailyAIQuota(path, private_root=private, clock=clock, limit=1).reserve()["used"] == 1
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT day, used FROM daily_attempts ORDER BY day").fetchall() == [
            ("2026-11-19", 1), ("2026-11-20", 1),
        ]


def test_clock_rollback_cannot_create_an_earlier_fresh_allowance(state):
    value = quota(state, limit=1)
    assert value.reserve()["used"] == 1
    state[2].instant = datetime(2026, 11, 18, 6, tzinfo=UTC)
    expect_error("ai_quota_clock_rollback", value.reserve)
    expect_error("ai_quota_clock_rollback", value.status)
    state[2].instant = datetime(2026, 11, 19, 6, tzinfo=UTC)
    assert value.status()["used"] == 1
    expect_error("ai_daily_limit_reached", value.reserve, 429)


def test_parallel_instances_do_not_exceed_the_shared_limit(state):
    def attempt(_):
        try:
            quota(state, lock_timeout=10).reserve()
            return 200
        except DomainError as error:
            assert error.code == "ai_daily_limit_reached"
            return error.status

    with ThreadPoolExecutor(max_workers=12) as pool:
        outcomes = list(pool.map(attempt, range(160)))
    assert Counter(outcomes) == {200: 100, 429: 60}
    assert quota(state).status()["used"] == 100


def test_independent_processes_share_limit_and_initial_creation_lock(state):
    private, path, _ = state
    source = Path(__file__).resolve().parents[1]
    script = '''import json,sys
from datetime import UTC,datetime
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from app.ai_quota import DailyAIQuota
from app.errors import DomainError
quota=DailyAIQuota(Path(sys.argv[2]),private_root=Path(sys.argv[3]),lock_timeout=10,
                  clock=lambda:datetime(2026,11,19,6,tzinfo=UTC))
out={'reserved':0,'blocked':0}
for _ in range(40):
    try:
        quota.reserve()
        out['reserved']+=1
    except DomainError as error:
        if error.code!='ai_daily_limit_reached' or error.status!=429:
            raise
        out['blocked']+=1
print(json.dumps(out))
'''
    processes = [subprocess.Popen(
        [sys.executable, "-I", "-c", script, str(source), str(path), str(private)],
        env={"PATH": "/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ) for _ in range(4)]
    totals = Counter()
    try:
        for process in processes:
            output, error = process.communicate(timeout=30)
            assert process.returncode == 0, error
            totals.update(json.loads(output))
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()
    assert totals == {"reserved": 100, "blocked": 60}
    assert quota(state).status()["used"] == 100


@pytest.mark.parametrize("change", ["delete", "empty", "corrupt"])
def test_existing_ledger_loss_or_corruption_never_resets_allowance(state, change):
    value = quota(state)
    value.reserve()
    path = state[1]
    if change == "delete":
        path.unlink()
    elif change == "empty":
        path.write_bytes(b"")
    else:
        path.write_bytes(b"not a SQLite database")
    expect_error("ai_quota_unavailable", quota(state).reserve)
    if change == "delete":
        assert not path.exists()
    else:
        assert path.read_bytes() == (b"" if change == "empty" else b"not a SQLite database")


def test_existing_database_without_matching_anchor_is_not_replaced(state):
    private, path, _ = state
    path.parent.mkdir(parents=True, mode=0o700)
    private.chmod(0o700)
    path.write_bytes(b"unrelated existing state")
    path.chmod(0o600)
    expect_error("ai_quota_unavailable", quota(state).reserve)
    assert path.read_bytes() == b"unrelated existing state"


@pytest.mark.parametrize("mutation", ["timezone", "version", "identity", "counter", "trigger"])
def test_inconsistent_state_or_unexpected_database_objects_fail_closed(state, mutation):
    value = quota(state)
    value.reserve()
    with sqlite3.connect(state[1]) as connection:
        if mutation == "timezone":
            connection.execute("UPDATE quota_meta SET value='UTC' WHERE key='timezone'")
        elif mutation == "version":
            connection.execute("PRAGMA user_version=99")
        elif mutation == "identity":
            connection.execute("UPDATE quota_meta SET value='other-state' WHERE key='instance_id'")
        elif mutation == "counter":
            connection.execute("PRAGMA ignore_check_constraints=ON")
            connection.execute("UPDATE daily_attempts SET used=101")
        else:
            connection.execute("CREATE TRIGGER altered AFTER UPDATE ON daily_attempts BEGIN SELECT 1; END")
    expect_error("ai_quota_unavailable", quota(state).reserve)


@pytest.mark.parametrize("target", ["root", "directory", "database", "lock", "journal"])
def test_insecure_existing_permissions_fail_closed(state, target):
    value = quota(state)
    value.reserve()
    private, path, _ = state
    candidates = {
        "root": private, "directory": path.parent, "database": path,
        "lock": value.lock_path, "journal": path.with_name(path.name + "-journal"),
    }
    selected = candidates[target]
    if target == "journal":
        selected.write_bytes(b"")
    selected.chmod(0o755 if target in {"root", "directory"} else 0o644)
    expect_error("ai_quota_unavailable", value.reserve)


@pytest.mark.parametrize("target", ["directory", "database", "lock", "-journal", "-wal", "-shm"])
def test_symlink_paths_are_rejected_before_reading_or_writing_target(state, tmp_path, target):
    private, path, _ = state
    outside = tmp_path / "unrelated"
    outside.write_bytes(b"unchanged unrelated state")
    outside.chmod(0o600)
    value = quota(state)
    if target == "directory":
        private.mkdir(mode=0o700)
        path.parent.symlink_to(tmp_path, target_is_directory=True)
    else:
        value.reserve()
        link = path if target == "database" else value.lock_path if target == "lock" else path.with_name(path.name + target)
        link.unlink(missing_ok=True)
        link.symlink_to(outside)
    expect_error("ai_quota_unavailable", value.reserve)
    assert outside.read_bytes() == b"unchanged unrelated state"


def test_hardlinked_state_is_rejected(state, tmp_path):
    value = quota(state)
    value.reserve()
    os.link(state[1], tmp_path / "other-copy")
    expect_error("ai_quota_unavailable", value.reserve)


@pytest.mark.parametrize("limit", [0, -1, 101, True, 1.5, "100"])
def test_limit_must_be_an_integer_between_one_and_a_hundred(state, limit):
    expect_error("ai_quota_unavailable", lambda: quota(state, limit=limit))


@pytest.mark.parametrize("clock", [lambda: datetime(2026, 11, 19), lambda: "2026-11-19"])
def test_invalid_clock_fails_closed(state, clock):
    private, path, _ = state
    value = DailyAIQuota(path, private_root=private, clock=clock)
    expect_error("ai_quota_unavailable", value.reserve)


def test_path_must_stay_within_injected_private_root(state, tmp_path):
    private, _, _ = state
    for path in (Path("relative.sqlite3"), tmp_path / "outside.sqlite3", private / "../escaped.sqlite3"):
        expect_error("ai_quota_unavailable", lambda: DailyAIQuota(path, private_root=private))
