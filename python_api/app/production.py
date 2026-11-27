"""CR-025 / T-045: explicit deployment state and TLS MySQL dependencies.

This module never chooses a local database or retrieves AWS credentials. The
deployment supplies the settings; startup verifies the existing schema later.
"""

from __future__ import annotations

import ipaddress
import os
import re
import ssl
import stat
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import certifi
import pymysql

from app.auth_store import MySQLAuthStore
from app.errors import DomainError
from app.manse_mysql import MySQLManseStore
from app.manse_store import configure_manse_store
from app.restored_fortune import MySQLRestoredFortuneStore, configure_restored_fortune_store
from app.source_archive import MySQLSourceArchiveStore, configure_source_archive_store

if TYPE_CHECKING:
    from app.config import Settings

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_HOST_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z")


def _configuration_error() -> RuntimeError:
    return RuntimeError("운영 환경의 WOONARI_DB_* 및 WOONARI_STATE_DIR 설정을 확인하세요.")


def _database_settings(settings: Settings) -> tuple[str, int, str, str]:
    """Validate required connection values without placing them in exceptions."""
    try:
        host = settings.woonari_db_host
        port = settings.woonari_db_port
        user = settings.woonari_db_user
        password = settings.woonari_db_password.get_secret_value()
        if (
            not isinstance(host, str) or host != host.strip() or not host
            or any(ord(char) < 33 for char in host)
            or type(port) is not int or not 1 <= port <= 65535
            or settings.woonari_db_name != "woonari"
            or not isinstance(user, str) or not user.strip() or "\0" in user
            or not isinstance(password, str) or not password or "\0" in password
        ):
            raise ValueError
        normalized_host = host.removesuffix(".")
        try:
            ipaddress.ip_address(normalized_host)
        except ValueError:
            if len(normalized_host) > 253 or not all(
                _HOST_LABEL.fullmatch(part) for part in normalized_host.split(".")
            ):
                raise ValueError from None
        return normalized_host, port, user, password
    except (AttributeError, TypeError, ValueError):
        raise _configuration_error() from None


def _check_ancestors(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISDIR(info.st_mode):
            raise _configuration_error()


def production_state_root(settings: Settings) -> Path:
    """Require a private, writable persistent location outside the package.

    Existing directories are never chmod'ed or reset. Only a deployment's
    explicitly selected missing state directory is created with private mode.
    """
    _database_settings(settings)
    try:
        value = settings.woonari_state_dir
        if value is None:
            raise ValueError
        path = Path(value)
        if (
            not path.is_absolute() or ".." in path.parts or path == Path(path.anchor)
            or path.is_relative_to(_PACKAGE_ROOT)
        ):
            raise ValueError
        _check_ancestors(path)
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        _check_ancestors(path)
        info = path.lstat()
        if stat.S_IMODE(info.st_mode) != 0o700 or info.st_uid != os.geteuid():
            raise ValueError
        with tempfile.TemporaryFile(dir=path) as probe:
            probe.write(b"1")
            probe.flush()
        return path
    except (OSError, TypeError, ValueError):
        raise _configuration_error() from None


def _tls_context(settings: Settings) -> ssl.SSLContext:
    try:
        supplied = settings.woonari_db_ca_file
        if supplied is None:
            ca_file = certifi.where()
        else:
            path = Path(supplied)
            if not path.is_absolute() or ".." in path.parts:
                raise ValueError
            # A public CA need not be owned by the API account, but must be an
            # ordinary file rather than a path that can redirect at runtime.
            current = Path(path.anchor)
            for part in path.parts[1:-1]:
                current /= part
                if not stat.S_ISDIR(current.lstat().st_mode):
                    raise ValueError
            if not stat.S_ISREG(path.lstat().st_mode):
                raise ValueError
            ca_file = str(path)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(cafile=ca_file)
        if not context.check_hostname or context.verify_mode != ssl.CERT_REQUIRED:
            raise ValueError
        return context
    except (OSError, ValueError, TypeError, AttributeError):
        raise RuntimeError("운영 데이터베이스 TLS 인증서 설정을 확인하세요.") from None


def build_mysql_runtime(settings: Settings) -> MySQLAuthStore:
    """Build shared explicit MySQL dependencies, without network or DDL."""
    host, port, user, password = _database_settings(settings)
    context = _tls_context(settings)

    def connect():
        try:
            return pymysql.connect(
                host=host, port=port, user=user, password=password.encode("utf-8"),
                database="woonari", ssl=context, charset="utf8mb4", autocommit=None,
                connect_timeout=5, read_timeout=5, write_timeout=5
            )
        except Exception:
            # Driver errors can contain connection values; never expose them.
            raise DomainError("database_unavailable", "운영 데이터베이스에 연결할 수 없습니다.", 503) from None

    store = MySQLAuthStore(connect)
    archive = MySQLSourceArchiveStore(connect)
    configure_manse_store(lambda: MySQLManseStore(connect))
    configure_restored_fortune_store(lambda: MySQLRestoredFortuneStore(connect))
    configure_source_archive_store(lambda: archive)
    return store


def verify_production_store(store: MySQLAuthStore) -> None:
    """Fail startup if production was given SQLite or an unusable schema."""
    if not isinstance(store, MySQLAuthStore):
        raise RuntimeError("운영 회원 저장소는 명시적인 MySQL 연결이 필요합니다.")
    try:
        store.verify()
    except Exception:
        raise RuntimeError("운영 회원 데이터베이스와 인증 스키마를 확인하세요.") from None
