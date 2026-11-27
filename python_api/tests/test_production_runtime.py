"""CR-025 / T-045: production configuration has no implicit local fallback."""

import shutil
import ssl
import stat
import traceback
from pathlib import Path
from types import SimpleNamespace

import certifi
import pytest
from pydantic import SecretStr

import app.production as production
from app.auth_store import MySQLAuthStore, SQLiteAuthStore
from app.errors import DomainError
from app.manse_mysql import MySQLManseStore
from app.restored_fortune import MySQLRestoredFortuneStore
from app.source_archive import MySQLSourceArchiveStore


def settings(tmp_path, **changes):
    values = {
        "woonari_env": "production",
        "woonari_state_dir": tmp_path / "state",
        "woonari_db_host": "mysql.example.invalid",
        "woonari_db_port": 3306,
        "woonari_db_name": "woonari",
        "woonari_db_user": "unit-db-user",
        "woonari_db_password": SecretStr("unit-db-password"),
        "woonari_db_ca_file": None
    }
    return SimpleNamespace(**(values | changes))


@pytest.fixture
def registrations(monkeypatch):
    values = {}
    monkeypatch.setattr(production, "configure_manse_store", lambda factory: values.update(manse=factory))
    monkeypatch.setattr(production, "configure_restored_fortune_store", lambda factory: values.update(restored=factory))
    monkeypatch.setattr(production, "configure_source_archive_store", lambda factory: values.update(archive=factory))
    return values


def test_explicit_state_is_private_persistent_and_does_not_touch_package(tmp_path):
    configured = settings(tmp_path)
    root = production.production_state_root(configured)
    assert root == configured.woonari_state_dir
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    marker = root / "existing-ledger-marker"
    marker.write_bytes(b"preserve-existing-state")
    assert production.production_state_root(configured) == root
    assert marker.read_bytes() == b"preserve-existing-state"
    assert set(root.iterdir()) == {marker}


@pytest.mark.parametrize("value", [None, Path("relative-state"), Path("/"), Path("/tmp/../state")])
def test_missing_or_ambiguous_state_path_is_rejected(tmp_path, value):
    with pytest.raises(RuntimeError, match="WOONARI_STATE_DIR"):
        production.production_state_root(settings(tmp_path, woonari_state_dir=value))


def test_package_directory_cannot_be_used_as_persistent_state(tmp_path):
    candidate = production._PACKAGE_ROOT / "not-a-runtime-state-directory"
    assert not candidate.exists()
    with pytest.raises(RuntimeError):
        production.production_state_root(settings(tmp_path, woonari_state_dir=candidate))
    assert not candidate.exists()


@pytest.mark.parametrize("ancestor", [False, True])
def test_state_symlinks_are_rejected_without_following_them(tmp_path, ancestor):
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    supplied = link / "state" if ancestor else link
    with pytest.raises(RuntimeError):
        production.production_state_root(settings(tmp_path, woonari_state_dir=supplied))
    assert list(target.iterdir()) == []


def test_state_cannot_be_an_existing_file(tmp_path):
    path = tmp_path / "state-file"
    path.write_bytes(b"must-preserve")
    with pytest.raises(RuntimeError):
        production.production_state_root(settings(tmp_path, woonari_state_dir=path))
    assert path.read_bytes() == b"must-preserve"


def test_insecure_existing_directory_is_not_chmodded(tmp_path):
    root = tmp_path / "public-state"
    root.mkdir(mode=0o755)
    root.chmod(0o755)
    with pytest.raises(RuntimeError):
        production.production_state_root(settings(tmp_path, woonari_state_dir=root))
    assert stat.S_IMODE(root.stat().st_mode) == 0o755


def test_state_must_be_owned_by_current_process_user(tmp_path, monkeypatch):
    root = tmp_path / "foreign-owned"
    root.mkdir(mode=0o700)
    expected_owner = root.stat().st_uid
    monkeypatch.setattr(production.os, "geteuid", lambda: expected_owner + 1)
    with pytest.raises(RuntimeError):
        production.production_state_root(settings(tmp_path, woonari_state_dir=root))


def test_writability_is_verified_without_exposing_os_error(tmp_path, monkeypatch):
    def denied(**kwargs):
        raise PermissionError("unit-private-filesystem-detail")
    monkeypatch.setattr(production.tempfile, "TemporaryFile", denied)
    with pytest.raises(RuntimeError) as caught:
        production.production_state_root(settings(tmp_path))
    assert "unit-private-filesystem-detail" not in str(caught.value)


@pytest.mark.parametrize("change", [
    {"woonari_db_host": ""},
    {"woonari_db_host": "https://mysql.example.invalid"},
    {"woonari_db_host": "user@mysql.example.invalid"},
    {"woonari_db_host": "mysql.example.invalid/path"},
    {"woonari_db_host": "bad\nhost"},
    {"woonari_db_host": " host.example.invalid"},
    {"woonari_db_host": "a" * 64 + ".example.invalid"},
    {"woonari_db_port": 0},
    {"woonari_db_port": 65536},
    {"woonari_db_port": True},
    {"woonari_db_user": ""},
    {"woonari_db_password": SecretStr("")},
    {"woonari_db_password": SecretStr("unit\0secret")},
    {"woonari_db_name": "another-project"}
])
def test_incomplete_or_unsafe_database_configuration_fails_before_state_write(tmp_path, change):
    with pytest.raises(RuntimeError):
        production.production_state_root(settings(tmp_path, **change))
    assert not (tmp_path / "state").exists()


def test_builder_does_not_connect_or_issue_ddl_and_wires_all_mysql_consumers(tmp_path, monkeypatch, registrations):
    calls = []
    connection = object()
    monkeypatch.setattr(production.pymysql, "connect", lambda **kwargs: calls.append(kwargs) or connection)
    configured = settings(tmp_path)
    store = production.build_mysql_runtime(configured)
    assert isinstance(store, MySQLAuthStore)
    assert calls == []
    assert isinstance(registrations["manse"](), MySQLManseStore)
    assert isinstance(registrations["restored"](), MySQLRestoredFortuneStore)
    first_archive = registrations["archive"]()
    assert isinstance(first_archive, MySQLSourceArchiveStore)
    assert registrations["archive"]() is first_archive
    assert calls == []
    assert store.connector() is connection
    assert registrations["manse"]().connector() is connection
    request = calls[0]
    assert request["database"] == "woonari"
    assert request["host"] == "mysql.example.invalid"
    assert request["user"] == "unit-db-user"
    assert request["password"] == b"unit-db-password"
    assert request["charset"] == "utf8mb4"
    assert request["autocommit"] is None
    assert request["connect_timeout"] == request["read_timeout"] == request["write_timeout"] == 5
    assert isinstance(request["ssl"], ssl.SSLContext)
    assert request["ssl"].check_hostname
    assert request["ssl"].verify_mode == ssl.CERT_REQUIRED


@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "MYSQL.EXAMPLE.INVALID."])
def test_valid_address_forms_are_passed_to_driver_as_addresses(tmp_path, host, monkeypatch, registrations):
    requests = []
    monkeypatch.setattr(production.pymysql, "connect", lambda **kwargs: requests.append(kwargs))
    store = production.build_mysql_runtime(settings(tmp_path, woonari_db_host=host))
    store.connector()
    assert requests[0]["host"] == host.removesuffix(".")


def test_connection_errors_never_return_credentials_or_endpoint(tmp_path, monkeypatch, registrations):
    def fail(**kwargs):
        raise RuntimeError("unit-db-password mysql.example.invalid unit-db-user")
    monkeypatch.setattr(production.pymysql, "connect", fail)
    store = production.build_mysql_runtime(settings(tmp_path))
    with pytest.raises(DomainError) as caught:
        store.connector()
    assert caught.value.code == "database_unavailable" and caught.value.status == 503
    rendered = "".join(traceback.format_exception(caught.type, caught.value, caught.tb))
    for private in ("unit-db-password", "mysql.example.invalid", "unit-db-user"):
        assert private not in rendered


def test_explicit_ca_is_used_and_insecure_environment_ca_is_ignored(tmp_path, monkeypatch, registrations):
    selected = tmp_path / "selected-ca.pem"
    shutil.copyfile(certifi.where(), selected)
    monkeypatch.setenv("SSL_CERT_FILE", str(tmp_path / "missing-certificate.pem"))
    requests = []
    monkeypatch.setattr(production.pymysql, "connect", lambda **kwargs: requests.append(kwargs))
    store = production.build_mysql_runtime(settings(tmp_path, woonari_db_ca_file=selected))
    store.connector()
    assert requests[0]["ssl"].check_hostname
    assert requests[0]["ssl"].verify_mode == ssl.CERT_REQUIRED


@pytest.mark.parametrize("kind", ["missing", "relative", "directory", "invalid", "symlink", "linked-parent"])
def test_invalid_explicit_ca_does_not_fall_back_to_default(tmp_path, kind, registrations):
    supplied = tmp_path / "ca.pem"
    if kind == "relative":
        supplied = Path("ca.pem")
    elif kind == "directory":
        supplied.mkdir()
    elif kind == "invalid":
        supplied.write_text("unit-invalid-private-certificate-data")
    elif kind in {"symlink", "linked-parent"}:
        target = tmp_path / "valid-ca.pem"
        shutil.copyfile(certifi.where(), target)
        if kind == "symlink":
            supplied.symlink_to(target)
        else:
            directory = tmp_path / "linked"
            directory.symlink_to(tmp_path, target_is_directory=True)
            supplied = directory / "valid-ca.pem"
    with pytest.raises(RuntimeError, match="TLS") as caught:
        production.build_mysql_runtime(settings(tmp_path, woonari_db_ca_file=supplied))
    assert str(supplied) not in str(caught.value)
    assert "unit-invalid-private-certificate-data" not in str(caught.value)
    assert registrations == {}


def test_production_does_not_accept_local_sqlite_even_with_valid_schema(tmp_path):
    store = SQLiteAuthStore(tmp_path / "auth.sqlite3")
    with pytest.raises(RuntimeError, match="MySQL"):
        production.verify_production_store(store)
    assert not (tmp_path / "auth.sqlite3").exists()


def test_startup_verifies_existing_mysql_schema_without_initializing_it():
    class VerifiedStore(MySQLAuthStore):
        def __init__(self):
            self.checked = False

        def verify(self):
            self.checked = True

        def initialize(self):
            raise AssertionError("startup must not issue DDL")

    store = VerifiedStore()
    production.verify_production_store(store)
    assert store.checked


def test_schema_error_details_are_suppressed_at_startup():
    class BrokenStore(MySQLAuthStore):
        def __init__(self):
            pass

        def verify(self):
            raise RuntimeError("unit-db-password mysql.example.invalid")

    with pytest.raises(RuntimeError) as caught:
        production.verify_production_store(BrokenStore())
    rendered = "".join(traceback.format_exception(caught.type, caught.value, caught.tb))
    assert "unit-db-password" not in rendered
    assert "mysql.example.invalid" not in rendered
