"""T-013: credential inheritance and foreign-process protection."""

import json
import signal

import isolated_runtime as runtime
import pytest


@pytest.fixture
def private_state(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "STATE", tmp_path)

    def private(path):
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        return path

    monkeypatch.setattr(runtime, "private_dir", private)
    return tmp_path


@pytest.fixture
def config():
    return {"project": "woonari", "api_port": 9090, "dashboard_port": 18101}


def test_api_environment_ignores_parent_and_does_not_expand_values(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-parent-key")
    monkeypatch.setenv("API_KEY", "synthetic-parent-api-key")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "synthetic-parent-aws-key")
    monkeypatch.setenv("GH_TOKEN", "synthetic-parent-github-key")
    path = tmp_path / "api.env"
    path.write_text('OPENAI_MODEL="${OPENAI_API_KEY}"\nAPI_KEY=synthetic-project-key\n')
    path.chmod(0o600)
    values = runtime.api_environment(path)
    assert values["OPENAI_API_KEY"] == ""
    assert values["OPENAI_MODEL"] == "${OPENAI_API_KEY}"
    assert values["API_KEY"] == "synthetic-project-key"
    environment = runtime.clean_env()
    assert not any(key.startswith(("OPENAI_", "AWS_", "GH_")) for key in environment)
    assert "API_KEY" not in environment


def test_missing_api_env_uses_all_five_explicit_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-parent-key")
    assert runtime.api_environment(tmp_path / "missing.env") == runtime.API_DEFAULTS


def test_api_env_rejects_unexpected_account_setting_without_echoing_secret(tmp_path):
    path = tmp_path / "api.env"
    path.write_text("AWS_SECRET_ACCESS_KEY=synthetic-project-secret\n")
    path.chmod(0o600)
    with pytest.raises(RuntimeError) as error:
        runtime.api_environment(path)
    assert "synthetic-project-secret" not in str(error.value)


def test_api_env_rejects_world_readable_file(tmp_path):
    path = tmp_path / "api.env"
    path.write_text("API_KEY=synthetic-project-secret\n")
    path.chmod(0o644)
    with pytest.raises(RuntimeError, match="600"):
        runtime.api_environment(path)


def test_api_env_rejects_symlink(tmp_path):
    source = tmp_path / "source.env"
    source.write_text("API_KEY=synthetic-project-secret\n")
    source.chmod(0o600)
    link = tmp_path / "api.env"
    link.symlink_to(source)
    with pytest.raises(RuntimeError, match="일반 파일"):
        runtime.api_environment(link)


def owned_record():
    instance = "a" * 32
    argv = ["/project/python", "/project/isolated_runtime.py", instance]
    return {
        "project": "woonari", "instance": instance, "pid": 10001,
        "started": "synthetic-start", "command": " ".join(argv), "argv": argv,
        "port": 9090,
    }


def test_recycled_pid_is_rejected_before_any_signal(config, monkeypatch):
    record = owned_record()
    monkeypatch.setattr(runtime, "specification", lambda *_: record)
    monkeypatch.setattr(runtime, "process_identity", lambda _: {
        "pid": record["pid"], "started": "different-start", "command": record["command"],
    })
    signals = []
    monkeypatch.setattr(runtime.os, "kill", lambda *args: signals.append(args))
    with pytest.raises(RuntimeError, match="기록과 다릅니다"):
        runtime.terminate_record("api", config, record)
    assert signals == []


def test_command_must_match_owned_full_invocation(config, monkeypatch):
    record = owned_record()
    record["command"] = "/unrelated-project/python same-looking-server"
    monkeypatch.setattr(runtime, "specification", lambda *_: record)
    monkeypatch.setattr(runtime, "process_identity", lambda _: {
        key: record[key] for key in ("pid", "started", "command")
    })
    with pytest.raises(RuntimeError, match="전용 실행 명령"):
        runtime.verify_record("api", config, record)


def test_stop_preflights_all_records_before_stopping_any(config, private_state, monkeypatch):
    monkeypatch.setattr(runtime, "read_record", lambda service: {"service": service})

    def verify(service, *_):
        if service == "dashboard":
            raise RuntimeError("foreign process")
        return {"pid": 10001}

    monkeypatch.setattr(runtime, "verify_record", verify)
    stopped = []
    monkeypatch.setattr(runtime, "terminate_record", lambda *args: stopped.append(args))
    with pytest.raises(RuntimeError, match="foreign process"):
        runtime.stop(config)
    assert stopped == []


def test_stop_signals_only_the_owned_pid(config, private_state, monkeypatch):
    record = owned_record()
    identity = {key: record[key] for key in ("pid", "started", "command")}
    monkeypatch.setattr(runtime, "verify_record", lambda *_: identity)
    monkeypatch.setattr(runtime, "process_identity", lambda _: None)
    signals = []
    monkeypatch.setattr(runtime.os, "kill", lambda *args: signals.append(args))
    runtime.terminate_record("api", config, record)
    assert signals == [(10001, signal.SIGTERM)]


def test_stop_does_not_kill_when_process_exits_before_final_check(
    config, private_state, monkeypatch,
):
    record = owned_record()
    identity = {key: record[key] for key in ("pid", "started", "command")}
    checks = iter((identity, None))
    monkeypatch.setattr(runtime, "verify_record", lambda *_: next(checks))
    ticks = iter((0, 6))
    monkeypatch.setattr(runtime.time, "monotonic", lambda: next(ticks))
    signals = []
    monkeypatch.setattr(runtime.os, "kill", lambda *args: signals.append(args))
    runtime.terminate_record("api", config, record)
    assert signals == [(10001, signal.SIGTERM)]


def test_port_conflict_never_launches_or_stops_process(config, private_state, monkeypatch):
    monkeypatch.setattr(runtime, "read_record", lambda _: None)
    monkeypatch.setattr(runtime, "specification", lambda *_: {"port": 9090})
    monkeypatch.setattr(runtime, "port_available", lambda _: False)
    calls = []
    monkeypatch.setattr(runtime, "launch", lambda *args: calls.append(args))
    monkeypatch.setattr(runtime.os, "kill", lambda *args: calls.append(args))
    with pytest.raises(RuntimeError, match="다른 프로세스"):
        runtime.start(config)
    assert calls == []


@pytest.mark.parametrize("port_free", [True, False])
def test_start_only_replaces_owned_api_after_new_port_is_available(
    config, private_state, monkeypatch, port_free,
):
    previous = owned_record()
    previous["port"] = 18100
    previous["argv"] = runtime.specification(
        "api", {**config, "api_port": 18100}, previous["instance"],
    )["argv"]
    previous["command"] = " ".join(previous["argv"])
    monkeypatch.setattr(runtime, "read_record", lambda service: previous if service == "api" else None)
    monkeypatch.setattr(runtime, "process_identity", lambda _: {
        key: previous[key] for key in ("pid", "started", "command")
    })
    monkeypatch.setattr(runtime, "port_available", lambda port: port_free or port != 9090)
    monkeypatch.setattr(runtime, "status", lambda _: 0)
    actions = []
    monkeypatch.setattr(runtime, "terminate_record", lambda name, *_: actions.append(("stop", name)))
    monkeypatch.setattr(runtime, "launch", lambda name, *_: actions.append(("start", name)))

    if not port_free:
        with pytest.raises(RuntimeError, match="9090"):
            runtime.start(config)
        assert actions == []
    else:
        assert runtime.start(config) == 0
        assert actions == [("stop", "api"), ("start", "api"), ("start", "dashboard")]


def test_existing_owned_services_are_reused(config, private_state, monkeypatch):
    record = owned_record()
    monkeypatch.setattr(runtime, "read_record", lambda _: record)
    monkeypatch.setattr(runtime, "verify_record", lambda *_: {"pid": 10001})
    monkeypatch.setattr(runtime, "responding", lambda *_: True)
    monkeypatch.setattr(runtime, "status", lambda _: 0)
    launched = []
    monkeypatch.setattr(runtime, "launch", lambda *args: launched.append(args))
    assert runtime.start(config) == 0
    assert launched == []


def test_response_from_another_server_is_not_accepted(monkeypatch):
    class Response:
        status = 200

        def __init__(self):
            self.headers = {"X-Woonari-Instance": "wrong-instance"}

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

    class Opener:
        def open(self, *_args, **_kwargs):
            return Response()

    monkeypatch.setattr(runtime.urllib.request, "build_opener", lambda *_: Opener())
    assert runtime.responding("api", 9090, "a" * 32) is False


def test_process_record_is_private_and_contains_no_environment(private_state):
    path = private_state / "record.json"
    record = owned_record()
    runtime.private_write(path, record)
    assert path.stat().st_mode & 0o077 == 0
    assert json.loads(path.read_text()) == record
    assert "environment" not in json.loads(path.read_text())


def test_read_record_rejects_foreign_project(private_state):
    folder = runtime.runtime_dir()
    (folder / "api.json").write_text(json.dumps({"project": "another-project", "pid": 10001}))
    with pytest.raises(RuntimeError, match="Woonari 프로세스 기록이 아닙니다"):
        runtime.read_record("api")
