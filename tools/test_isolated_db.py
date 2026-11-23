"""T-015: exercise the TLS and secret boundaries without AWS or MySQL calls."""

import json
import ssl
import subprocess
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import isolated_db as db
import pytest

SECRET = {
    "host": "mysql.example.test",
    "username": "fixture-user",
    "password": "fixture-sensitive-value!한글",
    "dbname": "fixture-db",
    "port": 3307,
}


@pytest.fixture(autouse=True)
def project_database_config(monkeypatch):
    original = db.database_config
    monkeypatch.setattr(db, "database_config", lambda: {
        "secret_arn": "", "database": "", "manse_backend": "sqlite",
    })
    return original


def envelope(secret):
    return json.dumps({"SecretString": json.dumps(secret)}).encode()


def test_secret_lookup_uses_only_project_wrapper_and_captures_output(monkeypatch):
    reference = "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:inter-AbCd12"
    monkeypatch.setattr(db, "database_config", lambda: {
        "secret_arn": reference, "database": "", "manse_backend": "sqlite",
    })
    environment = {"PATH": "/usr/bin:/bin"}
    monkeypatch.setattr(db, "clean_env", lambda: environment)
    runner = Mock(return_value=subprocess.CompletedProcess([], 0, envelope(SECRET), b""))
    monkeypatch.setattr(db.subprocess, "run", runner)

    settings = db._read_secret()

    command = runner.call_args.args[0]
    assert command[:4] == [str(db.ROOT / "woonari"), "aws", "secretsmanager", "get-secret-value"]
    assert command[command.index("--secret-id") + 1] == reference
    assert command[command.index("--version-stage") + 1] == "AWSCURRENT"
    assert command[command.index("--region") + 1] == "ap-southeast-2"
    assert runner.call_args.kwargs["env"] == environment
    assert runner.call_args.kwargs["capture_output"] is True
    assert runner.call_args.kwargs["timeout"] > 0
    assert settings == {
        "host": "mysql.example.test", "user": "fixture-user", "password": SECRET["password"],
        "database": "fixture-db", "port": 3307,
    }


def test_scp_denial_masks_raw_error_and_never_loads_driver(monkeypatch, capsys):
    stderr = b"AccessDeniedException: explicit deny in a service control policy: private-fixture"
    result = subprocess.CompletedProcess([], 255, b"private-fixture", stderr)
    monkeypatch.setattr(db.subprocess, "run", Mock(return_value=result))
    driver = Mock()
    monkeypatch.setattr(db, "_driver", driver)

    assert db.main(["check"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "AWS Organizations SCP" in output.err
    assert "private-fixture" not in output.err
    driver.assert_not_called()


def test_aliases_and_mysql_default_port():
    secret = {
        "DB_HOST": SECRET["host"], "db_username": SECRET["username"],
        "passwd": SECRET["password"], "database": SECRET["dbname"],
    }
    assert db._secret_fields(envelope(secret)) == {
        "host": SECRET["host"], "user": SECRET["username"],
        "password": SECRET["password"], "database": SECRET["dbname"], "port": 3306,
    }


def test_unspecified_database_is_not_inferred():
    settings = db._secret_fields(envelope({key: value for key, value in SECRET.items() if key != "dbname"}))
    assert "database" not in settings


@pytest.mark.parametrize(
    "secret, message",
    [
        ({**SECRET, "engine": "postgres"}, "MySQL 엔진"),
        ({**SECRET, "dbname": ""}, "database 필드"),
        ({**SECRET, "port": True}, "port는"),
        ({**SECRET, "port": "65536"}, "port는"),
        ({**SECRET, "host": "mysql://fixture"}, "host는"),
        ({**SECRET, "db_password": "other-private-fixture"}, "별칭 값"),
    ],
)
def test_malformed_secret_is_rejected_without_values(secret, message):
    with pytest.raises(db.DatabaseCheckError, match=message) as caught:
        db._secret_fields(envelope(secret))
    assert SECRET["password"] not in str(caught.value)
    assert "other-private-fixture" not in str(caught.value)


def test_smoke_check_uses_verified_tls_executes_select_one_and_closes(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(db, "private_dir", lambda _: tmp_path)
    monkeypatch.setattr(db, "_read_secret", lambda: db._secret_fields(envelope(SECRET)))
    driver = Mock()
    connection = driver.connect.return_value
    cursor = Mock()
    connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
    connection.cursor.return_value.__exit__ = Mock(return_value=False)
    cursor.fetchone.return_value = (1,)
    monkeypatch.setattr(db, "_driver", lambda: driver)

    assert db.main(["check"]) == 0
    options = driver.connect.call_args.kwargs
    context = options["ssl"]
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    assert context.minimum_version == ssl.TLSVersion.TLSv1_2
    assert options["password"] == SECRET["password"].encode()
    assert options["database"] == SECRET["dbname"]
    assert options["autocommit"] is None
    cursor.execute.assert_called_once_with("SELECT 1")
    connection.close.assert_called_once_with()
    assert SECRET["password"] not in capsys.readouterr().out


def test_inherited_tls_key_logging_is_not_enabled(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "private_dir", lambda _: tmp_path)
    keylog = tmp_path / "shared-keylog.txt"
    monkeypatch.setenv("SSLKEYLOGFILE", str(keylog))

    context = db._tls_context(SECRET["host"])

    assert context.keylog_filename is None
    assert not keylog.exists()


@pytest.mark.parametrize(
    "host, expected",
    [
        ("db.id.ap-northeast-2.rds.amazonaws.com", "rds-global-bundle.pem"),
        ("proxy-db.id.ap-northeast-2.rds.amazonaws.com", "rds-global-bundle.pem"),
        ("db.proxy-id.ap-northeast-2.rds.amazonaws.com", "public.pem"),
        ("db.example.test", "mysql-ca.pem"),
    ],
)
def test_tls_trust_file_selection(host, expected, monkeypatch, tmp_path):
    for name in ("rds-global-bundle.pem", "public.pem", "mysql-ca.pem"):
        (tmp_path / name).touch()
    monkeypatch.setattr(db, "private_dir", lambda _: tmp_path)
    monkeypatch.setattr(db.certifi, "where", lambda: str(tmp_path / "public.pem"))
    create_context = Mock()
    monkeypatch.setattr(db.ssl, "SSLContext", create_context)

    db._tls_context(host)

    create_context.assert_called_once_with(ssl.PROTOCOL_TLS_CLIENT)
    create_context.return_value.load_verify_locations.assert_called_once_with(
        cafile=str(tmp_path / expected),
    )


def test_driver_refuses_non_tls_before_sending_authentication(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "private_dir", lambda _: tmp_path)
    driver = db._driver()
    connection = driver.connections.Connection(
        host=SECRET["host"], user=SECRET["username"], password=SECRET["password"].encode(),
        ssl=db._tls_context(SECRET["host"]), defer_connect=True,
    )
    connection.server_version = "8.0.40"
    connection.server_capabilities = 0
    packet = Mock()
    monkeypatch.setattr(connection, "write_packet", packet)

    with pytest.raises(driver.err.OperationalError) as caught:
        connection._request_authentication()

    assert caught.value.args[0] == 2026
    packet.assert_not_called()


def test_query_failure_masks_driver_detail_and_closes(monkeypatch, capsys):
    connection = Mock()
    cursor = Mock()
    cursor.execute.side_effect = RuntimeError(1142, SECRET["password"])
    connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
    connection.cursor.return_value.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(db, "connect_mysql", lambda: connection)

    assert db.main(["check"]) == 1

    output = capsys.readouterr()
    assert output.out == ""
    assert "쿼리 권한" in output.err
    assert SECRET["password"] not in output.err
    connection.close.assert_called_once_with()


def test_wrapped_ssl_verification_error_is_classified_without_details():
    error = RuntimeError(2003, SECRET["host"])
    error.original_exception = ssl.SSLCertVerificationError(SECRET["host"])
    assert str(db._mysql_error(error)) == db.TLS_ERROR


def test_explicit_database_override_preserves_other_secret_alias_checks():
    secret = {**SECRET, "database": "other-fixture-db"}
    assert db._secret_fields(envelope(secret), database="woonari")["database"] == "woonari"
    with pytest.raises(db.DatabaseCheckError, match="별칭 값"):
        db._secret_fields(envelope({**secret, "db_password": "other-fixture-value"}), database="woonari")


def test_secret_lookup_uses_private_database_override(monkeypatch):
    monkeypatch.setattr(db, "database_config", lambda: {
        "secret_arn": "", "database": "woonari", "manse_backend": "mysql",
    })
    runner = Mock(return_value=subprocess.CompletedProcess([], 0, envelope(SECRET), b""))
    monkeypatch.setattr(db.subprocess, "run", runner)
    assert db._read_secret()["database"] == "woonari"


def write_database_config(tmp_path, settings):
    directory = tmp_path / "db"
    directory.mkdir(exist_ok=True)
    path = directory / "config.json"
    path.write_text(json.dumps(settings), encoding="utf-8")
    path.chmod(0o600)
    return path


def test_private_database_config_accepts_only_designated_account(
    monkeypatch, tmp_path, project_database_config,
):
    monkeypatch.setattr(db, "STATE", tmp_path)
    monkeypatch.setattr(db, "load_config", lambda: {"aws": {"account_id": "123456789012"}})
    settings = {
        "secret_arn": "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:inter-AbCd12",
        "database": "woonari", "manse_backend": "mysql",
    }
    write_database_config(tmp_path, settings)
    assert project_database_config() == settings


def test_private_database_config_rejects_foreign_secret_account(
    monkeypatch, tmp_path, project_database_config,
):
    monkeypatch.setattr(db, "STATE", tmp_path)
    monkeypatch.setattr(db, "load_config", lambda: {"aws": {"account_id": "123456789012"}})
    write_database_config(tmp_path, {
        "secret_arn": "arn:aws:secretsmanager:ap-southeast-2:999999999999:secret:inter-AbCd12",
        "database": "woonari", "manse_backend": "mysql",
    })
    with pytest.raises(db.DatabaseCheckError, match="시크릿 계정"):
        project_database_config()


@pytest.mark.parametrize("settings", [
    {"database": None}, {"secret_arn": 0}, {"database": "bad-name"},
    {"manse_backend": "unknown"}, {"password": "private-fixture"},
    {"secret_arn": "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:unrelated-AbCd12"},
])
def test_private_database_config_rejects_invalid_shape_and_values(
    settings, monkeypatch, tmp_path, project_database_config,
):
    monkeypatch.setattr(db, "STATE", tmp_path)
    monkeypatch.setattr(db, "load_config", lambda: {"aws": {"account_id": "123456789012"}})
    write_database_config(tmp_path, settings)
    with pytest.raises(db.DatabaseCheckError) as caught:
        project_database_config()
    assert "private-fixture" not in str(caught.value)


def test_private_database_config_rejects_shared_permissions_and_symlinks(
    monkeypatch, tmp_path, project_database_config,
):
    monkeypatch.setattr(db, "STATE", tmp_path)
    path = write_database_config(tmp_path, {"database": "woonari"})
    path.chmod(0o644)
    with pytest.raises(db.DatabaseCheckError):
        project_database_config()
    path.unlink()
    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_text('{"database":"woonari"}', encoding="utf-8")
    elsewhere.chmod(0o600)
    path.symlink_to(elsewhere)
    with pytest.raises(db.DatabaseCheckError):
        project_database_config()


@pytest.mark.parametrize("database", ["", None, "bad-name", "db`; SELECT 1", "x" * 65, "1db"])
def test_connector_rejects_invalid_database_before_loading_any_credentials(database, monkeypatch):
    secret = Mock()
    monkeypatch.setattr(db, "_read_secret", secret)
    with pytest.raises(db.DatabaseCheckError):
        db.mysql_connector(database)
    secret.assert_not_called()


def connector_mocks(monkeypatch, *, secrets=None):
    settings = db._secret_fields(envelope(SECRET))
    reader = Mock(side_effect=secrets) if secrets else Mock(return_value=settings)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    tls = Mock(return_value=context)
    driver = Mock()
    driver.connect.side_effect = lambda **_kwargs: Mock()
    monkeypatch.setattr(db, "_read_secret", reader)
    monkeypatch.setattr(db, "_tls_context", tls)
    monkeypatch.setattr(db, "_driver", lambda: driver)
    return reader, tls, driver, context


def test_connector_reuses_secret_and_tls_in_memory_but_returns_new_connections(monkeypatch):
    reader, tls, driver, context = connector_mocks(monkeypatch)
    connect = db.mysql_connector("woonari")
    reader.assert_not_called()
    first, second = connect(), connect()
    assert first is not second
    first.close.assert_not_called()
    second.close.assert_not_called()
    reader.assert_called_once_with()
    tls.assert_called_once_with(SECRET["host"])
    assert driver.connect.call_count == 2
    options = driver.connect.call_args.kwargs
    assert options["database"] == "woonari"
    assert options["ssl"] is context
    assert options["ssl"].verify_mode == ssl.CERT_REQUIRED
    assert options["ssl"].check_hostname is True
    assert options["password"] == SECRET["password"].encode()
    assert options["connect_timeout"] == options["read_timeout"] == options["write_timeout"] == 5


def test_connector_refreshes_rotated_secret_at_five_minute_expiry(monkeypatch):
    first = db._secret_fields(envelope(SECRET))
    second = {**first, "password": "rotated-fixture-value"}
    reader, tls, driver, _context = connector_mocks(monkeypatch, secrets=[first, second])
    now = [10.0]
    monkeypatch.setattr(db.time, "monotonic", lambda: now[0])
    connect = db.mysql_connector("woonari")
    connect()
    now[0] = 309.999
    connect()
    assert reader.call_count == 1
    now[0] = 310.0
    connect()
    assert reader.call_count == tls.call_count == 2
    assert driver.connect.call_args.kwargs["password"] == second["password"].encode()


def test_connector_refresh_is_synchronized_across_concurrent_requests(monkeypatch):
    reader, tls, driver, _context = connector_mocks(monkeypatch)
    connect = db.mysql_connector("woonari")
    with ThreadPoolExecutor(max_workers=4) as pool:
        connections = list(pool.map(lambda _: connect(), range(8)))
    assert len({id(connection) for connection in connections}) == 8
    assert reader.call_count == tls.call_count == 1
    assert driver.connect.call_count == 8


def test_connector_refresh_failure_does_not_use_expired_credentials(monkeypatch):
    settings = db._secret_fields(envelope(SECRET))
    reader, _tls, driver, _context = connector_mocks(monkeypatch, secrets=[
        settings, RuntimeError(SECRET["password"]), settings,
    ])
    now = [0.0]
    monkeypatch.setattr(db.time, "monotonic", lambda: now[0])
    connect = db.mysql_connector("woonari")
    connect()
    now[0] = 301.0
    with pytest.raises(db.DatabaseCheckError, match="인증 설정") as caught:
        connect()
    assert SECRET["password"] not in str(caught.value)
    assert driver.connect.call_count == 1
    connect()
    assert reader.call_count == 3
    assert driver.connect.call_count == 2


def test_connector_driver_failure_uses_safe_error_without_logging_credentials(monkeypatch, capsys):
    _reader, _tls, driver, _context = connector_mocks(monkeypatch)
    driver.connect.side_effect = RuntimeError(1045, SECRET["password"])
    with pytest.raises(db.DatabaseCheckError, match="로그인 인증") as caught:
        db.mysql_connector("woonari")()
    assert SECRET["password"] not in str(caught.value)
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_connect_mysql_can_ignore_secret_database_for_creating_target_schema(monkeypatch):
    _reader, _tls, driver, _context = connector_mocks(monkeypatch)
    db.connect_mysql(select_database=False)
    assert driver.connect.call_args.kwargs["database"] is None
