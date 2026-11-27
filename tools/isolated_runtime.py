"""T-013 / F06: start only Woonari-owned, loopback-only local services."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from contextlib import contextmanager
from pathlib import Path

from project_context import (
    API_PORT,
    ROOT,
    STATE,
    clean_env,
    fail,
    load_config,
    private_dir,
)

API_DEFAULTS = {
    "AI_PROVIDER": "openai",
    "BEDROCK_MODEL_ID": "",
    "BEDROCK_REGION": "",
    "BEDROCK_AUTH_MODE": "iam",
    "BEDROCK_ACCOUNT_ID": "",
    "BEDROCK_MAX_TOKENS": "8192",
    "AI_DAILY_CALL_LIMIT": "100",
    "OPENAI_API_KEY": "",
    "OPENAI_MODEL": "",
    "AI_TIMEOUT_SECONDS": "45",
    "AI_MAX_CONCURRENCY": "4",
    "API_KEY": "",
}
SERVICES = ("api", "dashboard")
PYTHON_ENV_FILE = ROOT / "python_api/.env"


def api_process_environment() -> dict[str, str]:
    """Canonical Python settings replace the legacy runtime config as one source."""
    environment = clean_env()
    if not PYTHON_ENV_FILE.exists() and not PYTHON_ENV_FILE.is_symlink():
        environment.update(api_environment(STATE / "api.env"))
    return environment


def runtime_dir() -> Path:
    return private_dir(STATE / "runtime")


def private_write(path: Path, value: dict) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def runtime_lock():
    descriptor = os.open(runtime_dir() / "runtime.lock", os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(descriptor, "a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def api_environment(path: Path) -> dict[str, str]:
    """Read dotenv without expansion, shell execution, or inherited app settings."""
    result = dict(API_DEFAULTS)
    if not path.exists():
        return result
    if path.is_symlink() or not path.is_file():
        fail("전용 api.env는 일반 파일이어야 합니다.")
    if path.stat().st_mode & 0o077:
        fail("전용 api.env 권한을 600으로 설정해 주세요.")
    parser = (
        "import io,json,sys; from dotenv import dotenv_values; "
        "print(json.dumps(dotenv_values(stream=io.StringIO(sys.stdin.read()), "
        "interpolate=False)))"
    )
    parsed = subprocess.run(
        [str(ROOT / "python_api/.venv/bin/python"), "-c", parser],
        input=path.read_text(encoding="utf-8"),
        text=True,
        capture_output=True,
        env=clean_env(),
        cwd=ROOT,
        check=False,
    )
    if parsed.returncode or parsed.stderr:
        fail("전용 api.env 형식을 확인해 주세요. 설정값은 출력하지 않습니다.")
    try:
        values = json.loads(parsed.stdout)
    except (ValueError, TypeError):
        fail("전용 api.env를 읽지 못했습니다.")
    if not isinstance(values, dict) or set(values) - set(API_DEFAULTS):
        fail("api.env에는 안내된 프로젝트 전용 AI/API 설정만 사용할 수 있습니다.")
    if any(not isinstance(value, str) for value in values.values()):
        fail("api.env의 모든 항목은 KEY=VALUE 형식이어야 합니다.")
    result.update(values)
    return result


def specification(service: str, config: dict, instance: str) -> dict:
    if service == "api":
        executable = ROOT / "python_api/.venv/bin/python"
        if not executable.is_file():
            fail("프로젝트 Python 가상환경이 없습니다. python_api/.venv를 준비해 주세요.")
        argv = [
            str(executable), str(ROOT / "tools/isolated_runtime.py"),
            "_serve-api", "--port", str(config["api_port"]), "--instance", instance,
        ]
        return {"argv": argv, "cwd": ROOT / "python_api", "port": config["api_port"]}
    node = shutil.which("node", path=clean_env().get("PATH", ""))
    if not node:
        fail("프로젝트 대시보드 실행에 Node.js가 필요합니다.")
    argv = [
        node, str(ROOT / "tools/dashboard-local.mjs"),
        "--port", str(config["dashboard_port"]), "--instance", instance,
    ]
    return {"argv": argv, "cwd": ROOT, "port": config["dashboard_port"]}


def process_identity(pid: int) -> dict | None:
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 1:
        return None
    identity = {"pid": pid}
    for field, option in (("started", "lstart="), ("command", "command=")):
        process = subprocess.run(
            ["/bin/ps", "-p", str(pid), "-o", option],
            capture_output=True, text=True, env=clean_env(), check=False,
        )
        if process.returncode:
            if "permitted" in process.stderr.lower() or "denied" in process.stderr.lower():
                fail("프로세스 확인 권한이 없어 실행/종료하지 않았습니다.")
            return None
        identity[field] = process.stdout.strip()
    return identity if identity["started"] and identity["command"] else None


def read_record(service: str) -> dict | None:
    path = runtime_dir() / f"{service}.json"
    if not path.exists():
        return None
    if path.is_symlink():
        fail("프로세스 기록이 심볼릭 링크이므로 처리하지 않았습니다.")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        fail("프로세스 기록이 손상되었습니다. 임의 프로세스는 종료하지 않습니다.")
    if not isinstance(value, dict) or value.get("project") != "woonari":
        fail("Woonari 프로세스 기록이 아닙니다. 임의 프로세스는 종료하지 않습니다.")
    return value


def verify_record(service: str, config: dict, record: dict) -> dict | None:
    instance = record.get("instance", "")
    if not isinstance(instance, str) or not re.fullmatch(r"[a-f0-9]{32}", instance):
        fail("프로세스 인스턴스 기록이 올바르지 않습니다.")
    if service == "api":
        port = record.get("port")
        if type(port) is not int or not 1024 <= port <= 65535:
            fail("API 프로세스 기록의 포트가 올바르지 않습니다.")
        # Verify the exact old invocation before stopping an API from an older install.
        config = {**config, "api_port": port}
    expected = specification(service, config, instance)
    if record.get("argv") != expected["argv"] or record.get("port") != expected["port"]:
        fail("현재 프로젝트 설정과 프로세스 기록이 달라 자동 처리하지 않았습니다.")
    current = process_identity(record.get("pid"))
    if current is None:
        return None
    if any(current[key] != record.get(key) for key in ("pid", "started", "command")):
        fail("PID의 실제 프로세스가 기록과 다릅니다. 다른 프로세스는 종료하지 않습니다.")
    # Verify the complete owned invocation, beyond merely trusting a saved PID/start time.
    if current["command"] != " ".join(expected["argv"]):
        fail("전용 실행 명령과 실제 프로세스가 달라 자동 처리하지 않았습니다.")
    return current


def port_available(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False


def responding(service: str, port: int, instance: str) -> bool:
    path = "/health" if service == "api" else "/api/version"
    # Ignore system/parent HTTP proxies even for localhost.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"http://127.0.0.1:{port}{path}", timeout=0.7) as response:
            return response.status == 200 and response.headers.get("X-Woonari-Instance") == instance
    except (OSError, urllib.error.URLError):
        return False


def launch(service: str, config: dict) -> dict:
    instance = uuid.uuid4().hex
    spec = specification(service, config, instance)
    environment = clean_env()
    if service == "api":
        environment = api_process_environment()
    logfile = runtime_dir() / f"{service}.log"
    if logfile.is_symlink():
        fail("로그 경로가 심볼릭 링크이므로 실행하지 않았습니다.")
    descriptor = os.open(logfile, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.chmod(logfile, 0o600)
    with os.fdopen(descriptor, "ab", buffering=0) as output:
        process = subprocess.Popen(
            spec["argv"], cwd=spec["cwd"], env=environment,
            stdin=subprocess.DEVNULL, stdout=output, stderr=output,
            start_new_session=True, close_fds=True,
        )
    record = None
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if process.poll() is not None:
                fail(f"{service}가 시작되지 않았습니다. 전용 로그를 확인해 주세요: {logfile}")
            if record is None:
                identity = process_identity(process.pid)
                if identity:
                    record = {
                        "project": "woonari", "service": service, "instance": instance,
                        "argv": spec["argv"], "port": spec["port"], **identity,
                    }
                    verify_record(service, config, record)
                    private_write(runtime_dir() / f"{service}.json", record)
            if record and responding(service, spec["port"], instance):
                return record
            time.sleep(0.1)
        fail(f"{service} 준비 시간이 초과되었습니다. 전용 로그를 확인해 주세요: {logfile}")
    except BaseException:
        # This Popen handle was created in this invocation; never terminate an arbitrary PID.
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        path = runtime_dir() / f"{service}.json"
        existing = read_record(service)
        if existing and existing.get("instance") == instance:
            path.unlink(missing_ok=True)
        raise


def start(config: dict) -> int:
    with runtime_lock():
        existing = {}
        previous_api = None
        # Preflight both services, so a conflict never causes a partial new start.
        for service in SERVICES:
            record = read_record(service)
            if record and verify_record(service, config, record):
                if service == "api" and record["port"] != API_PORT:
                    previous_api = record
                else:
                    if not responding(service, record["port"], record["instance"]):
                        fail(f"{service} 전용 프로세스가 응답하지 않습니다. 먼저 전용 stop을 실행해 주세요.")
                    existing[service] = record
                    continue
            elif record:
                (runtime_dir() / f"{service}.json").unlink()
            spec = specification(service, config, "0" * 32)
            if not port_available(spec["port"]):
                fail(f"포트 {spec['port']}를 다른 프로세스가 사용 중입니다. 자동 종료하지 않습니다.")
        if previous_api:
            terminate_record("api", config, previous_api)
        for service in SERVICES:
            if service not in existing:
                launch(service, config)
    return status(config)


def terminate_record(service: str, config: dict, record: dict) -> None:
    current = verify_record(service, config, record)
    if current:
        os.kill(current["pid"], signal.SIGTERM)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if process_identity(current["pid"]) != current:
                break
            time.sleep(0.1)
        else:
            # Recheck identity immediately before escalating termination of our own service.
            if verify_record(service, config, record):
                os.kill(current["pid"], signal.SIGKILL)
    (runtime_dir() / f"{service}.json").unlink(missing_ok=True)


def stop(config: dict) -> int:
    with runtime_lock():
        # Validate every live PID before stopping either service.
        records = {service: read_record(service) for service in SERVICES}
        for service, record in records.items():
            if record:
                verify_record(service, config, record)
        for service, record in records.items():
            if record:
                terminate_record(service, config, record)
    print("Woonari 전용 프로세스를 종료했습니다. 다른 프로젝트는 변경하지 않았습니다.")
    return 0


def status(config: dict) -> int:
    services = {}
    api_port = API_PORT
    for service in SERVICES:
        record = read_record(service)
        if record and verify_record(service, config, record):
            if service == "api":
                api_port = record["port"]
            ready = responding(service, record["port"], record["instance"])
            services[service] = {"status": "running" if ready else "unready", "pid": record["pid"]}
        else:
            services[service] = {"status": "stopped"}
    result = {
        "project": "woonari", "bind": "127.0.0.1", "services": services,
        "swagger": f"http://127.0.0.1:{api_port}/docs",
        "dashboard": f"http://127.0.0.1:{config['dashboard_port']}/",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def serve_api(args: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--instance", required=True)
    options = parser.parse_args(args)
    if options.port != API_PORT or not re.fullmatch(r"[a-f0-9]{32}", options.instance):
        fail("잘못된 전용 API 실행 인수입니다.")
    environment = api_process_environment()
    os.environ.clear()
    os.environ.update(environment)
    sys.path.insert(0, str(ROOT / "python_api"))
    import uvicorn
    from app.main import create_app

    if PYTHON_ENV_FILE.exists() or PYTHON_ENV_FILE.is_symlink():
        # create_app owns all DB, social and AI dependencies from Python settings.
        # No legacy secret files, AWS CLI profile or ambient app keys are consulted.
        application = create_app()
        return run_api(application, options.instance, uvicorn)

    from app.auth_settings import load_local_auth_settings
    from app.auth_store import MySQLAuthStore, SQLiteAuthStore
    from app.config import Settings
    from app.manse_store import configure_manse_store
    from app.restored_fortune import (
        MySQLRestoredFortuneStore,
        configure_restored_fortune_store,
    )
    from app.source_archive import (
        MySQLSourceArchiveStore,
        configure_source_archive_store,
    )
    from isolated_db import database_config, mysql_connector

    database = database_config()
    if database["manse_backend"] == "mysql":
        from app.manse_mysql import MySQLManseStore

        if not database["database"]:
            fail("MySQL 만세력 연결에 전용 DB 이름이 필요합니다.")
        connector = mysql_connector(database["database"])
        auth_store = MySQLAuthStore(connector)
        configure_manse_store(lambda: MySQLManseStore(connector))
        configure_restored_fortune_store(lambda: MySQLRestoredFortuneStore(connector))
        source_archive = MySQLSourceArchiveStore(connector)
        configure_source_archive_store(lambda: source_archive)
    else:
        auth_store = SQLiteAuthStore(STATE / "auth/auth.sqlite3")
        configure_manse_store(None)
        configure_restored_fortune_store(None)
        configure_source_archive_store(None)

    try:
        settings = Settings(_env_file=None)
    except ValueError:
        fail("전용 AI/API 설정의 형식과 허용 범위를 확인하세요. 설정값은 출력하지 않습니다.")
    from app.ai_quota import DailyAIQuota

    quota = DailyAIQuota(
        STATE / "ai/usage.sqlite3", private_root=STATE, limit=settings.ai_daily_call_limit,
    )
    if settings.ai_provider == "bedrock":
        from app.bedrock import BedrockInterpreter
        from isolated_bedrock import make_bedrock_invoker

        invoker = make_bedrock_invoker(
            model_id=settings.bedrock_model_id,
            region=settings.bedrock_region,
            timeout=settings.ai_timeout_seconds,
            auth_mode=settings.bedrock_auth_mode,
            expected_account_id=settings.bedrock_account_id,
            reserve_call=quota.reserve,
        )
        application = create_app(
            settings,
            interpreter_factory=lambda configured: BedrockInterpreter(configured, invoker=invoker),
            ai_quota=quota,
            auth_settings=load_local_auth_settings(),
            auth_store=auth_store,
        )
    else:
        application = create_app(
            settings, ai_quota=quota,
            auth_settings=load_local_auth_settings(), auth_store=auth_store
        )

    return run_api(application, options.instance, uvicorn)


def run_api(application, instance: str, uvicorn) -> int:
    @application.middleware("http")
    async def owned_instance(request, call_next):
        response = await call_next(request)
        response.headers["X-Woonari-Instance"] = instance
        return response

    uvicorn.run(application, host="127.0.0.1", port=API_PORT, access_log=False)
    return 0


def main(args: list[str]) -> int:
    if args and args[0] == "_serve-api":
        return serve_api(args[1:])
    parser = argparse.ArgumentParser(prog="woonari runtime")
    parser.add_argument("command", choices=("start", "stop", "status"))
    options = parser.parse_args(args)
    config = load_config()
    return {"start": start, "stop": stop, "status": status}[options.command](config)


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (RuntimeError, OSError) as error:
        print(f"Woonari: {error}", file=sys.stderr)
        raise SystemExit(1)
