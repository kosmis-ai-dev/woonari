"""T-015 / CR-007: verify MySQL with Woonari's AWS Secrets Manager secret."""

from __future__ import annotations

import ipaddress
import json
import re
import ssl
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

import certifi

if __name__ == "__main__":
    # `python -I` omits the script directory. Import only the Woonari tools.
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from project_context import ROOT, STATE, clean_env, load_config, private_dir

if TYPE_CHECKING:
    from pymysql.connections import Connection

SECRET_NAME = "inter"
FIELDS = {
    "engine": ("engine", "db_engine"),
    "host": ("host", "hostname", "endpoint", "db_host", "mysql_host"),
    "user": ("username", "user", "db_user", "db_username", "mysql_user"),
    "password": ("password", "passwd", "db_password", "mysql_password"),
    "database": ("dbname", "database", "db_name", "db", "mysql_database"),
    "port": ("port", "db_port", "mysql_port"),
}
DB_ERRORS = {
    1044: "MySQL 데이터베이스 접근 권한을 확인해 주세요.",
    1045: "MySQL 로그인 인증이 거부되었습니다.",
    1049: "MySQL에 지정된 데이터베이스가 없습니다.",
    1142: "MySQL 쿼리 권한이 거부되었습니다.",
    1143: "MySQL 쿼리 권한이 거부되었습니다.",
    1227: "MySQL 쿼리 권한이 거부되었습니다.",
    1251: "MySQL 로그인 인증 방식을 확인해 주세요.",
    1698: "MySQL 로그인 인증이 거부되었습니다.",
    2059: "MySQL 로그인 인증 방식을 확인해 주세요.",
    2061: "MySQL 로그인 인증 방식을 확인해 주세요.",
}
TLS_ERROR = "MySQL TLS 연결 또는 서버 인증서 검증에 실패했습니다."
NETWORK_ERROR = "MySQL 네트워크 연결에 실패했습니다. DB 접근 경로와 방화벽을 확인해 주세요."
SECRET_CACHE_SECONDS = 300


class DatabaseCheckError(RuntimeError):
    """A public-facing error that contains no connection or secret values."""


def _unique_keys(pairs: list[tuple[str, object]]) -> dict:
    values = {}
    for key, value in pairs:
        normalized = key.casefold()
        if normalized in values:
            raise DatabaseCheckError("시크릿 inter에 중복 필드가 있습니다.")
        values[normalized] = value
    return values


def database_config() -> dict:
    """Only project-private, non-credential settings select the secret and schema."""
    path = STATE / "db/config.json"
    result = {"secret_arn": "", "database": "", "manse_backend": "sqlite"}
    if not path.exists():
        return result
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077:
            raise ValueError
        settings = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(settings, dict) or set(settings) - set(result):
            raise ValueError
        result.update(settings)
        if any(not isinstance(value, str) for value in result.values()):
            raise ValueError
        if result["manse_backend"] not in ("sqlite", "mysql"):
            raise ValueError
        if result["database"] and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", result["database"]):
            raise ValueError
        if result["secret_arn"]:
            match = re.fullmatch(
                r"arn:aws:secretsmanager:([a-z]{2}(?:-[a-z]+)+-\d+):(\d{12}):secret:inter-[A-Za-z0-9]+",
                result["secret_arn"],
            )
            if not match or match[2] != load_config()["aws"]["account_id"]:
                raise ValueError
    except (OSError, TypeError, ValueError):
        raise DatabaseCheckError("전용 DB 설정 형식·권한 또는 시크릿 계정을 확인해 주세요.") from None
    return result


def _secret_fields(stdout: bytes, *, database: str = "") -> dict:
    try:
        response = json.loads(stdout)
        secret = json.loads(response["SecretString"], object_pairs_hook=_unique_keys)
    except (ValueError, KeyError, TypeError, RecursionError):
        raise DatabaseCheckError("시크릿 inter의 SecretString에 JSON 객체가 필요합니다.") from None
    if not isinstance(secret, dict):
        raise DatabaseCheckError("시크릿 inter의 SecretString에 JSON 객체가 필요합니다.")
    fields = {}
    for field, aliases in FIELDS.items():
        if field == "database" and database:
            fields[field] = database
            continue
        values = [secret[alias] for alias in aliases if alias in secret]
        if values:
            first = values[0]
            if any(type(value) is not type(first) or value != first for value in values[1:]):
                raise DatabaseCheckError(f"시크릿 inter의 {field} 별칭 값이 서로 다릅니다.")
            fields[field] = first
    engine = fields.pop("engine", "mysql")
    if not isinstance(engine, str) or engine.strip().lower() not in {"mysql", "aurora-mysql"}:
        raise DatabaseCheckError("시크릿 inter에 MySQL 엔진을 지정해 주세요.")
    for field in ("host", "user", "password", "database"):
        if field == "database" and field not in fields:
            continue
        value = fields.get(field)
        if not isinstance(value, str) or not value.strip() or "\0" in value:
            raise DatabaseCheckError(f"시크릿 inter에 유효한 {field} 필드가 필요합니다.")
    host = fields["host"].strip().removesuffix(".")
    if not _valid_host(host):
        raise DatabaseCheckError("시크릿 inter의 host는 호스트명 또는 IP 주소여야 합니다.")
    port = fields.get("port", 3306)
    if isinstance(port, str) and re.fullmatch(r"[0-9]{1,5}", port.strip()):
        port = int(port.strip())
    if type(port) is not int or not 1 <= port <= 65535:
        raise DatabaseCheckError("시크릿 inter의 port는 1~65535 사이의 정수여야 합니다.")
    return {**fields, "host": host, "port": port}


def _valid_host(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        label = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        return len(host) <= 253 and all(re.fullmatch(label, part) for part in host.split("."))
    return True


def _read_secret() -> dict:
    config = database_config()
    reference = config["secret_arn"] or SECRET_NAME
    region = ["--region", reference.split(":")[3]] if config["secret_arn"] else []
    try:
        result = subprocess.run(
            [
                str(ROOT / "woonari"), "aws", "secretsmanager", "get-secret-value",
                "--secret-id", reference, *region,
                "--version-stage", "AWSCURRENT",
                "--output", "json", "--no-cli-pager",
                "--cli-connect-timeout", "5", "--cli-read-timeout", "10",
            ],
            cwd=ROOT,
            env=clean_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=50,
        )
    except subprocess.TimeoutExpired:
        raise DatabaseCheckError("AWS 시크릿 inter 조회 시간이 초과되었습니다.") from None
    except OSError:
        raise DatabaseCheckError("Woonari의 AWS 시크릿 조회 명령을 실행하지 못했습니다.") from None
    if result.returncode:
        reason = result.stderr.lower()
        if b"explicit deny" in reason and b"service control policy" in reason:
            raise DatabaseCheckError("AWS Organizations SCP가 시크릿 inter 조회를 명시적으로 거부했습니다.")
        if b"accessdenied" in reason or b"not authorized" in reason:
            raise DatabaseCheckError("AWS에서 시크릿 inter 조회 권한이 거부되었습니다.")
        if b"resourcenotfoundexception" in reason:
            raise DatabaseCheckError("Woonari AWS 계정의 설정된 리전에서 시크릿 inter를 찾지 못했습니다.")
        raise DatabaseCheckError("시크릿 inter 조회에 실패했습니다. Woonari 전용 AWS 인증과 권한을 확인해 주세요.")
    return _secret_fields(result.stdout, database=config["database"])


def _tls_context(host: str) -> ssl.SSLContext:
    try:
        directory = private_dir(STATE / "db")
        hostname = host.lower()
        rds = hostname.endswith((".rds.amazonaws.com", ".rds.amazonaws.com.cn"))
        proxy = any(label.startswith("proxy-") for label in hostname.split(".")[1:])
        if rds and not proxy:
            certificate = directory / "rds-global-bundle.pem"
            if not certificate.is_file() or certificate.is_symlink():
                raise DatabaseCheckError("전용 DB 설정 폴더에 AWS RDS CA 번들이 필요합니다.")
        elif rds:
            # RDS Proxy presents an ACM certificate trusted by the public CA store.
            certificate = Path(certifi.where())
        else:
            custom = directory / "mysql-ca.pem"
            if custom.is_symlink() or (custom.exists() and not custom.is_file()):
                raise DatabaseCheckError("전용 mysql-ca.pem은 일반 인증서 파일이어야 합니다.")
            certificate = custom if custom.is_file() else Path(certifi.where())
        # Client context verifies the certificate chain and hostname. Load only
        # the selected CA file and never honor SSLKEYLOGFILE from a caller.
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(cafile=str(certificate))
    except DatabaseCheckError:
        raise
    except (OSError, RuntimeError, ValueError):
        raise DatabaseCheckError("MySQL 서버 인증서 검증용 CA를 불러오지 못했습니다.") from None
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def _driver():
    try:
        import pymysql
    except ImportError:
        raise DatabaseCheckError("Woonari Python 가상환경에 PyMySQL을 설치해 주세요.") from None
    if pymysql.VERSION[:3] < (1, 2, 1):
        raise DatabaseCheckError("TLS 검증을 위해 Woonari의 PyMySQL 1.2.1 이상이 필요합니다.")
    return pymysql


def _mysql_error(error: Exception) -> DatabaseCheckError:
    errno = error.args[0] if error.args and type(error.args[0]) is int else None
    related = (error, getattr(error, "original_exception", None), error.__context__)
    if errno in {2026, 3159} or any(isinstance(exc, ssl.SSLError) for exc in related):
        return DatabaseCheckError(TLS_ERROR)
    if errno in DB_ERRORS:
        return DatabaseCheckError(DB_ERRORS[errno])
    if errno in {2002, 2003, 2005, 2006, 2013} or isinstance(error, OSError):
        return DatabaseCheckError(NETWORK_ERROR)
    return DatabaseCheckError("MySQL 연결 또는 SELECT 1 검증에 실패했습니다.")


def _open_mysql(settings: dict, context: ssl.SSLContext, database: str | None) -> Connection:
    driver = _driver()
    try:
        return driver.connect(
            host=settings["host"],
            port=settings["port"],
            user=settings["user"],
            password=settings["password"].encode("utf-8"),
            database=database,
            ssl=context,
            charset="utf8mb4",
            autocommit=None,
            connect_timeout=5,
            read_timeout=5,
            write_timeout=5,
        )
    except Exception as error:  # noqa: BLE001 - driver exceptions can include connection values
        raise _mysql_error(error) from None


def connect_mysql(*, select_database: bool = True) -> Connection:
    """Open a TLS-verified connection. The caller owns and closes it."""
    settings = _read_secret()
    context = _tls_context(settings["host"])
    database = settings.get("database") if select_database else None
    return _open_mysql(settings, context, database)


def mysql_connector(database: str) -> Callable[[], Connection]:
    """Create fresh connections, refreshing project secret and TLS settings every five minutes."""
    if not isinstance(database, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", database):
        raise DatabaseCheckError("유효한 Woonari MySQL 데이터베이스 이름이 필요합니다.")
    refresh_lock = threading.Lock()
    settings = None
    context = None
    expires_at = 0.0

    def connect() -> Connection:
        nonlocal settings, context, expires_at
        with refresh_lock:
            if settings is None or time.monotonic() >= expires_at:
                try:
                    refreshed = _read_secret()
                    refreshed_context = _tls_context(refreshed["host"])
                except DatabaseCheckError:
                    raise
                except Exception:  # noqa: BLE001 - credentials never enter error messages
                    raise DatabaseCheckError("MySQL 인증 설정을 갱신하지 못했습니다.") from None
                settings = refreshed
                context = refreshed_context
                expires_at = time.monotonic() + SECRET_CACHE_SECONDS
            current_settings = settings
            current_context = context
        return _open_mysql(current_settings, current_context, database)

    return connect


def check_database() -> None:
    connection = connect_mysql()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                raise DatabaseCheckError("MySQL SELECT 1의 응답을 확인하지 못했습니다.")
    except DatabaseCheckError:
        raise
    except Exception as error:  # noqa: BLE001 - driver exceptions can include connection values
        raise _mysql_error(error) from None
    finally:
        # Preserve the check result if the driver already closed the socket.
        with suppress(Exception):
            connection.close()


def main(args: list[str]) -> int:
    if args != ["check"]:
        print("사용법: ./woonari db check", file=sys.stderr)
        return 2
    try:
        check_database()
    except DatabaseCheckError as error:
        print(f"Woonari DB: {error}", file=sys.stderr)
        return 1
    except Exception:  # noqa: BLE001 - never write raw exceptions to this CLI's output
        print("Woonari DB: 연결 확인 도구 실행에 실패했습니다.", file=sys.stderr)
        return 1
    print("Woonari MySQL TLS 연결 및 SELECT 1 성공.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        raise SystemExit(130) from None
