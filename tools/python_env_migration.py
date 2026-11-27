"""CR-025 / T-045: migrate private runtime settings into Python's own .env.

Only an explicit CLI invocation reads the existing credential sources. Values
never enter command arguments, diagnostics, or the returned migration report.
"""

from __future__ import annotations

import io
import json
import os
import re
import stat
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_api"))
sys.path.insert(0, str(ROOT / "tools"))

import bedrock_key
import certifi
import isolated_db
import isolated_runtime
from app.auth_settings import AuthSettings
from app.config import Settings
from dotenv.parser import parse_stream
from project_context import STATE

PYTHON_ENV_FILE = ROOT / "python_api/.env"
AUTH_FIELDS = (
    "AUTH_PUBLIC_BASE_URL", "KAKAO_CLIENT_ID", "KAKAO_CLIENT_SECRET",
    "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET",
)
ERROR = "Python API 설정 이전에 실패했습니다. 전용 설정의 형식·권한·접속 권한을 확인하세요. 설정값은 출력하지 않습니다."
FILE_LIMIT = 1024 * 1024


def _checked_parents(path: Path) -> None:
    if not path.is_absolute() or not path.is_relative_to(ROOT):
        raise ValueError
    current = ROOT
    for component in path.relative_to(ROOT).parts[:-1]:
        current /= component
        if current.is_symlink():
            raise ValueError
        if current.exists() and (not current.is_dir() or current.stat().st_uid != os.geteuid()):
            raise ValueError


def _read_private(path: Path) -> tuple[bytes | None, tuple | None]:
    """Read one owned, private regular file without following links."""
    _checked_parents(path)
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        # A broken symlink is still an invalid source or target.
        if path.is_symlink():
            raise ValueError
        return None, None
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_uid != os.geteuid() or info.st_nlink != 1 or info.st_size > FILE_LIMIT
        ):
            raise ValueError
        content = stream.read(FILE_LIMIT + 1)
    if len(content) > FILE_LIMIT:
        raise ValueError
    return content, (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size)


def _parse(content: bytes | None) -> dict[str, tuple[str, str | None]]:
    entries = {}
    if content is None:
        return entries
    for item in parse_stream(io.StringIO(content.decode("utf-8"))):
        if item.error:
            raise ValueError
        if item.key is None:
            continue
        key = item.key.upper()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", item.key) or key in entries:
            raise ValueError
        if item.value is not None and "\0" in item.value:
            raise ValueError
        entries[key] = (item.key, item.value)
    return entries


def _social_settings(entries: dict) -> AuthSettings:
    selected = {key.lower(): entries[key][1] for key in AUTH_FIELDS if key in entries}
    if selected:
        return AuthSettings(**selected)
    legacy = STATE / "auth/providers.env"
    content, _ = _read_private(legacy)
    values = _parse(content)
    if set(values) - set(AUTH_FIELDS) or any(value is None for _, value in values.values()):
        raise ValueError
    return AuthSettings(**{key.lower(): value for key, (_, value) in values.items()})


def _database_ca(host: str) -> Path:
    """Match isolated_db's direct RDS, RDS Proxy, and custom-CA selection."""
    hostname = host.lower()
    rds = hostname.endswith((".rds.amazonaws.com", ".rds.amazonaws.com.cn"))
    proxy = any(label.startswith("proxy-") for label in hostname.split(".")[1:])
    if rds and not proxy:
        selected = STATE / "db/rds-global-bundle.pem"
    elif rds:
        selected = Path(certifi.where())
    else:
        custom = STATE / "db/mysql-ca.pem"
        if custom.is_symlink() or (custom.exists() and not custom.is_file()):
            raise ValueError
        selected = custom if custom.is_file() else Path(certifi.where())
    if selected.is_symlink() or not selected.is_file():
        raise ValueError
    return selected.absolute()


def _runtime_values() -> dict[str, str]:
    _read_private(STATE / "api.env")
    values = isolated_runtime.api_environment(STATE / "api.env")
    if not isinstance(values, dict) or any(
        not isinstance(key, str) or not isinstance(value, str) for key, value in values.items()
    ):
        raise ValueError
    values = dict(values)
    if values.get("AI_PROVIDER") == "bedrock" and values.get("BEDROCK_AUTH_MODE") == "api_key":
        values[bedrock_key.KEY_NAME] = bedrock_key.read_api_key()
    # A stale canonical key must not enable a mode selected by another source.
    else:
        values[bedrock_key.KEY_NAME] = ""
    values.update({"WOONARI_ENV": "development", "WOONARI_STATE_DIR": str(STATE)})
    _read_private(STATE / "db/config.json")
    db = isolated_db.database_config()
    backend = db["manse_backend"]
    if backend not in {"sqlite", "mysql"}:
        raise ValueError
    values["WOONARI_DB_BACKEND"] = backend
    if backend == "mysql":
        if db["database"] != "woonari":
            raise ValueError
        secret = isolated_db._read_secret()
        if secret.get("database") != "woonari":
            raise ValueError
        values.update({
            "WOONARI_DB_HOST": secret["host"], "WOONARI_DB_PORT": str(secret["port"]),
            "WOONARI_DB_NAME": "woonari", "WOONARI_DB_USER": secret["user"],
            "WOONARI_DB_PASSWORD": secret["password"],
            "WOONARI_DB_CA_FILE": str(_database_ca(secret["host"])),
        })
    return values


def _serialize(entries: dict) -> bytes:
    lines = ["# Woonari Python API configuration. Keep private; never commit this file."]
    for key in sorted(entries):
        name, value = entries[key]
        if value is None:
            lines.append(name)
            continue
        if not isinstance(value, str) or "\0" in value:
            raise ValueError
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        escaped = escaped.replace("\n", "\\n").replace("\r", "\\r")
        lines.append(f'{name}="{escaped}"')
    return ("\n".join(lines) + "\n").encode("utf-8")


def _backup_directory() -> Path:
    if STATE != ROOT / ".local/woonari":
        raise ValueError
    current = ROOT
    for component in (".local", "woonari", "config-backups"):
        current /= component
        if current.is_symlink():
            raise ValueError
        current.mkdir(mode=0o700, exist_ok=True)
        info = current.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise ValueError
    return current


def _write_new(path: Path, content: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _replace(content: bytes, previous: bytes | None, identity: tuple | None) -> bool:
    directory = _backup_directory()
    if previous is not None:
        _write_new(directory / f"python-api-env-{uuid.uuid4().hex}.bak", previous)
    temporary = PYTHON_ENV_FILE.with_name(f".env-migration-{uuid.uuid4().hex}")
    try:
        _write_new(temporary, content)
        # Refuse to overwrite an edit or link introduced after the source read.
        _, current_identity = _read_private(PYTHON_ENV_FILE)
        if current_identity != identity:
            raise ValueError
        os.replace(temporary, PYTHON_ENV_FILE)
    finally:
        temporary.unlink(missing_ok=True)
    return previous is not None


def migrate_runtime_settings() -> dict:
    """Return field names and flags only, while preserving all original sources."""
    try:
        if (
            not ROOT.is_absolute() or ROOT.is_symlink()
            or STATE != ROOT / ".local/woonari"
            or PYTHON_ENV_FILE != ROOT / "python_api/.env"
            or PYTHON_ENV_FILE.parent.is_symlink() or not PYTHON_ENV_FILE.parent.is_dir()
        ):
            raise ValueError
        previous, identity = _read_private(PYTHON_ENV_FILE)
        entries = _parse(previous)
        auth = _social_settings(entries)
        for key in AUTH_FIELDS:
            value = getattr(auth, key.lower())
            entries[key] = (key, value.get_secret_value() if hasattr(value, "get_secret_value") else value)
        for key, value in _runtime_values().items():
            entries[key] = (key, value)
        # Supply every default explicitly so inherited terminal settings cannot
        # alter validation or become part of the migrated private file.
        known = {name: field.get_default(call_default_factory=True) for name, field in Settings.model_fields.items()}
        known.update({key.lower(): value for key, (_, value) in entries.items() if key.lower() in known})
        Settings(_env_file=None, **known)
        content = _serialize(entries)
        if _parse(content) != entries:
            raise ValueError
        backed_up = _replace(content, previous, identity)
        return {
            "settings_file": "python_api/.env", "backup_created": backed_up,
            "field_names": sorted(entries),
            "configured": {
                "bedrock_api_key": bool(entries[bedrock_key.KEY_NAME][1]),
                "mysql": entries["WOONARI_DB_BACKEND"][1] == "mysql",
                "kakao": auth.configured("kakao"), "google": auth.configured("google"),
                "naver": auth.configured("naver"),
            },
            "legacy_sources_preserved": True,
        }
    except Exception:  # noqa: BLE001 - upstream credential errors must never expose values
        raise RuntimeError(ERROR) from None


def main() -> int:
    try:
        print(json.dumps(migrate_runtime_settings(), ensure_ascii=False, indent=2))
        return 0
    except Exception:  # noqa: BLE001 - CLI diagnostics contain no private configuration values
        print(f"Woonari: {ERROR}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
