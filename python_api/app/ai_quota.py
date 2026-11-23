"""CR-013 / T-027: persistent, project-local AI invocation reservations.

Reserve immediately before each upstream attempt. A completed reservation is
never refunded, including when the provider rejects or times out. This ledger
stores dates and aggregate counts only; it never receives prompts or secrets.
"""

from __future__ import annotations

import errno
import fcntl
import os
import re
import sqlite3
import stat
import time
import uuid
from contextlib import ExitStack, contextmanager
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Callable
from urllib.parse import quote
from zoneinfo import ZoneInfo

from app.errors import DomainError

KST = ZoneInfo("Asia/Seoul")
_MARKER = b"woonari-ai-quota-v1 "
_APPLICATION_ID = 0x574E4151
_SCHEMA = {
    "quota_meta": "CREATE TABLE quota_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID",
    "daily_attempts": (
        "CREATE TABLE daily_attempts (day TEXT PRIMARY KEY, used INTEGER NOT NULL "
        "CHECK(typeof(used) = 'integer' AND used BETWEEN 0 AND 100)) WITHOUT ROWID"
    ),
}


def _unavailable() -> DomainError:
    return DomainError(
        "ai_quota_unavailable", "AI 호출 한도 기록을 확인할 수 없어 호출을 중단했습니다.", 503
    )


def _sql(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


class DailyAIQuota:
    """Atomic reservations shared by all processes using this private ledger.

    ``private_root`` must be the injected project state directory. All private
    directories must be owned by the current OS user with mode 700, and files
    must be mode 600. The durable lock marker prevents silently recreating a
    deleted database as an empty allowance on a later process restart.
    """

    def __init__(
        self,
        path: Path,
        *,
        private_root: Path,
        limit: int = 100,
        clock: Callable[[], datetime] | None = None,
        lock_timeout: float = 5,
    ):
        self.path = Path(path)
        self.private_root = Path(private_root)
        if (
            not self.path.is_absolute()
            or not self.private_root.is_absolute()
            or ".." in self.path.parts
            or ".." in self.private_root.parts
            or not self.path.is_relative_to(self.private_root)
            or self.path == self.private_root
            or type(limit) is not int
            or not 1 <= limit <= 100
            or type(lock_timeout) not in (int, float)
            or not 0 < lock_timeout <= 10
        ):
            raise _unavailable()
        self.limit = limit
        self.clock = clock or (lambda: datetime.now(UTC))
        self.lock_timeout = lock_timeout
        self.lock_path = self.path.with_name(self.path.name + ".lock")

    @staticmethod
    def _file_info(path: Path, *, missing: bool = False):
        try:
            info = path.lstat()
        except FileNotFoundError:
            if missing:
                return None
            raise
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_uid != os.geteuid()
            or info.st_nlink != 1
        ):
            raise _unavailable()
        return info

    def _prepare_parent(self):
        current = Path(self.path.anchor)
        for component in self.path.parent.parts[1:]:
            current /= component
            try:
                current.mkdir(mode=0o700)
            except FileExistsError:
                pass
            info = current.lstat()
            if not stat.S_ISDIR(info.st_mode):
                raise _unavailable()
            if current.is_relative_to(self.private_root) and (
                stat.S_IMODE(info.st_mode) != 0o700 or info.st_uid != os.geteuid()
            ):
                raise _unavailable()

    def _check_sidecars(self):
        for suffix in ("-journal", "-wal", "-shm"):
            self._file_info(self.path.with_name(self.path.name + suffix), missing=True)

    @contextmanager
    def _lock(self):
        self._prepare_parent()
        descriptor = os.open(
            self.lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600
        )
        try:
            info = os.fstat(descriptor)
            actual = self._file_info(self.lock_path)
            if (info.st_dev, info.st_ino) != (actual.st_dev, actual.st_ino):
                raise _unavailable()
            deadline = time.monotonic() + self.lock_timeout
            while True:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as error:
                    if error.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                        raise
                    if time.monotonic() >= deadline:
                        raise _unavailable() from None
                    time.sleep(0.01)
            marker = os.pread(descriptor, 128, 0)
            info = self._file_info(self.path, missing=True)
            if not marker:
                if info is not None:
                    # Existing ledgers without our durable marker are never
                    # imported, repaired or replaced as an empty allowance.
                    raise _unavailable()
                identity = uuid.uuid4().hex
                os.pwrite(descriptor, _MARKER + identity.encode("ascii") + b"\n", 0)
                os.fsync(descriptor)
                handle = os.open(
                    self.path, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
                )
                os.close(handle)
                fresh = True
            else:
                if (
                    len(marker) != len(_MARKER) + 33
                    or not marker.startswith(_MARKER)
                    or not re.fullmatch(rb"[0-9a-f]{32}\n", marker[len(_MARKER):])
                    or info is None
                    or info.st_size == 0
                ):
                    raise _unavailable()
                identity = marker[len(_MARKER):-1].decode("ascii")
                fresh = False
            self._check_sidecars()
            info = self._file_info(self.path)
            yield identity, fresh, (info.st_dev, info.st_ino)
        finally:
            os.close(descriptor)

    def _today(self) -> date:
        try:
            instant = self.clock()
            if not isinstance(instant, datetime) or instant.utcoffset() is None:
                raise ValueError
            return instant.astimezone(KST).date()
        except Exception:
            raise _unavailable() from None

    @staticmethod
    def _initialize(connection: sqlite3.Connection, identity: str):
        for statement in _SCHEMA.values():
            connection.execute(statement)
        connection.executemany(
            "INSERT INTO quota_meta(key, value) VALUES (?, ?)",
            (("schema_version", "1"), ("timezone", "Asia/Seoul"),
             ("instance_id", identity), ("max_day", "")),
        )
        connection.execute(f"PRAGMA application_id={_APPLICATION_ID}")
        connection.execute("PRAGMA user_version=1")

    @staticmethod
    def _validate(connection: sqlite3.Connection, identity: str) -> dict:
        if connection.execute("PRAGMA quick_check(1)").fetchone() != ("ok",):
            raise _unavailable()
        objects = connection.execute("SELECT type, name, sql FROM sqlite_master").fetchall()
        actual = {name: _sql(statement) for kind, name, statement in objects if kind == "table"}
        if (
            len(objects) != len(_SCHEMA)
            or actual != {name: _sql(statement) for name, statement in _SCHEMA.items()}
            or connection.execute("PRAGMA application_id").fetchone() != (_APPLICATION_ID,)
            or connection.execute("PRAGMA user_version").fetchone() != (1,)
        ):
            raise _unavailable()
        meta = dict(connection.execute("SELECT key, value FROM quota_meta"))
        if set(meta) != {"schema_version", "timezone", "instance_id", "max_day"} or (
            meta["schema_version"] != "1" or meta["timezone"] != "Asia/Seoul"
            or meta["instance_id"] != identity
        ):
            raise _unavailable()
        maximum = date.fromisoformat(meta["max_day"]) if meta["max_day"] else None
        if maximum and maximum.isoformat() != meta["max_day"]:
            raise _unavailable()
        for day, used in connection.execute("SELECT day, used FROM daily_attempts"):
            parsed = date.fromisoformat(day)
            if parsed.isoformat() != day or not maximum or parsed > maximum or (
                type(used) is not int or not 0 <= used <= 100
            ):
                raise _unavailable()
        return meta

    def _access(self, reserve: bool) -> dict:
        try:
            with ExitStack() as stack:
                identity, fresh, inode = stack.enter_context(self._lock())
                uri = "file:" + quote(str(self.path), safe="/") + "?mode=rw"
                connection = sqlite3.connect(
                    uri, uri=True, timeout=self.lock_timeout, isolation_level=None
                )
                # Roll back/close the SQLite transaction before releasing the
                # cross-process lock, including quota rejection and failures.
                stack.callback(connection.close)
                connection.execute("PRAGMA trusted_schema=OFF")
                connection.execute("PRAGMA temp_store=MEMORY")
                connection.execute("PRAGMA synchronous=FULL")
                if connection.execute("PRAGMA journal_mode").fetchone() != ("delete",):
                    raise _unavailable()
                connection.execute("BEGIN IMMEDIATE")
                if fresh:
                    self._initialize(connection, identity)
                meta = self._validate(connection, identity)
                today = self._today()
                day = today.isoformat()
                if meta["max_day"] and day < meta["max_day"]:
                    raise DomainError(
                        "ai_quota_clock_rollback",
                        "AI 호출 기록보다 현재 날짜가 이전입니다. 서버 시간을 확인해 주세요.", 503,
                    )
                if day > meta["max_day"]:
                    connection.execute("UPDATE quota_meta SET value=? WHERE key='max_day'", (day,))
                row = connection.execute(
                    "SELECT used FROM daily_attempts WHERE day=?", (day,)
                ).fetchone()
                used = row[0] if row else 0
                if reserve:
                    if used >= self.limit:
                        raise DomainError(
                            "ai_daily_limit_reached",
                            f"오늘 AI 호출 한도({self.limit}회)를 모두 사용했습니다. "
                            "한국시간 자정 이후 다시 시도해 주세요.", 429,
                        )
                    used += 1
                    connection.execute(
                        "INSERT INTO daily_attempts(day, used) VALUES (?, ?) "
                        "ON CONFLICT(day) DO UPDATE SET used=excluded.used", (day, used),
                    )
                result = {
                    "limit": self.limit, "used": used, "remaining": max(0, self.limit - used),
                    "date": day, "timezone": "Asia/Seoul",
                    "reset_at": datetime.combine(today + timedelta(days=1), datetime.min.time(), KST).isoformat(),
                }
                info = self._file_info(self.path)
                if (info.st_dev, info.st_ino) != inode:
                    raise _unavailable()
                self._check_sidecars()
                connection.execute("COMMIT")
                return result
        except DomainError:
            raise
        except (OSError, sqlite3.Error, TypeError, ValueError, OverflowError):
            raise _unavailable() from None

    def reserve(self) -> dict:
        """Durably consume one attempt, or raise 429/503 before upstream I/O."""
        return self._access(True)

    def status(self) -> dict:
        """Return aggregate usage without consuming an invocation attempt."""
        return self._access(False)
