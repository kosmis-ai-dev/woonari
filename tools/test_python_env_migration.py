"""CR-025 / T-045: private runtime migration without live credentials or calls."""

import json
import os
import stat
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import python_env_migration as migration
from app.config import Settings, _literal_env_values


def write_private(path, content):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)
    return path


@pytest.fixture
def environment(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    state = root / ".local/woonari"
    canonical = root / "python_api/.env"
    canonical.parent.mkdir()
    state.mkdir(mode=0o700, parents=True)
    (root / ".local").chmod(0o700)
    monkeypatch.setattr(migration, "ROOT", root)
    monkeypatch.setattr(migration, "STATE", state)
    monkeypatch.setattr(migration, "PYTHON_ENV_FILE", canonical)
    api = dict(migration.isolated_runtime.API_DEFAULTS)
    api_reader = Mock(side_effect=lambda _: dict(api))
    database = {"database": "woonari", "manse_backend": "sqlite"}
    db_reader = Mock(side_effect=lambda: dict(database))
    secret_reader = Mock(side_effect=AssertionError("No live secret access"))
    key_reader = Mock(side_effect=AssertionError("No live Bedrock key access"))
    monkeypatch.setattr(migration.isolated_runtime, "api_environment", api_reader)
    monkeypatch.setattr(migration.isolated_db, "database_config", db_reader)
    monkeypatch.setattr(migration.isolated_db, "_read_secret", secret_reader)
    monkeypatch.setattr(migration.bedrock_key, "read_api_key", key_reader)
    ca = root / "public-ca.pem"
    ca.write_text("unit public CA")
    monkeypatch.setattr(migration.certifi, "where", lambda: str(ca))
    return SimpleNamespace(
        root=root, state=state, canonical=canonical, api=api, database=database,
        api_reader=api_reader, db_reader=db_reader, secret_reader=secret_reader,
        key_reader=key_reader, ca=ca,
    )


def values(environment):
    return _literal_env_values(environment.canonical)


def test_new_file_contains_runtime_and_all_social_fields_without_ambient_values(environment, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "unit-ambient-should-not-migrate")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "unit-ambient-oauth")
    monkeypatch.setenv("WOONARI_ENV", "unit-invalid-ambient-mode")
    result = migration.migrate_runtime_settings()
    data = values(environment)
    assert set(migration.AUTH_FIELDS) <= set(data)
    assert set(environment.api) <= set(data)
    assert data["WOONARI_ENV"] == "development"
    assert data["WOONARI_STATE_DIR"] == str(environment.state)
    assert data["WOONARI_DB_BACKEND"] == "sqlite"
    assert data["AWS_BEARER_TOKEN_BEDROCK"] == ""
    assert data["OPENAI_API_KEY"] == "" and data["GOOGLE_CLIENT_ID"] == ""
    assert stat.S_IMODE(environment.canonical.stat().st_mode) == 0o600
    assert result["backup_created"] is False
    assert not any(result["configured"].values())
    environment.secret_reader.assert_not_called()
    environment.key_reader.assert_not_called()


def test_mysql_bedrock_migration_round_trips_quotes_dollars_and_newlines(environment, monkeypatch):
    password = 'unit-$VALUE-${VALUE}-"double"-\'single\'-\\path\nsecond\rthird\ttab'
    bearer = "unit-bearer-${KEEP}-$KEEP"
    environment.api.update({"AI_PROVIDER": "bedrock", "BEDROCK_AUTH_MODE": "api_key"})
    environment.database["manse_backend"] = "mysql"
    environment.secret_reader.side_effect = None
    environment.secret_reader.return_value = {
        "host": "unit-db.example.invalid", "port": 3310, "user": "unit-user",
        "password": password, "database": "woonari",
    }
    environment.key_reader.side_effect = None
    environment.key_reader.return_value = bearer
    monkeypatch.setenv("VALUE", "unit-must-not-expand")
    monkeypatch.setenv("KEEP", "unit-must-not-expand")
    result = migration.migrate_runtime_settings()
    data = values(environment)
    assert data["WOONARI_DB_PASSWORD"] == password
    assert data["AWS_BEARER_TOKEN_BEDROCK"] == bearer
    assert data["WOONARI_DB_PORT"] == "3310"
    assert data["WOONARI_DB_NAME"] == "woonari"
    assert data["WOONARI_DB_CA_FILE"] == str(environment.ca)
    cfg = Settings(_env_file=environment.canonical)
    assert cfg.woonari_db_password.get_secret_value() == password
    assert cfg.aws_bearer_token_bedrock.get_secret_value() == bearer
    report = json.dumps(result)
    assert password not in report and bearer not in report and "unit-user" not in report
    assert result["configured"]["mysql"] and result["configured"]["bedrock_api_key"]
    environment.secret_reader.assert_called_once_with()
    environment.key_reader.assert_called_once_with()


def test_preserves_canonical_oauth_extras_and_original_sources_with_private_backup(environment):
    original = (
        '# retained values\nKAKAO_CLIENT_ID=unit-canonical-id\n'
        'KAKAO_CLIENT_SECRET="unit-canonical-${KEEP}"\n'
        'custom_EXTRA="unit-$EXTRA-\\\"quoted\\\""\nAPI_KEY=unit-stale-api-key\n'
    )
    write_private(environment.canonical, original)
    legacy = write_private(environment.state / "auth/providers.env", "GOOGLE_CLIENT_ID=unit-legacy\n")
    api_file = write_private(environment.state / "api.env", "OPENAI_MODEL=unit-model\n")
    ledger = write_private(environment.state / "ai/usage.sqlite3", "unit-usage-do-not-reset")
    sources = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in (legacy, api_file, ledger)}
    result = migration.migrate_runtime_settings()
    data = values(environment)
    assert data["KAKAO_CLIENT_ID"] == "unit-canonical-id"
    assert data["KAKAO_CLIENT_SECRET"] == "unit-canonical-${KEEP}"
    assert data["GOOGLE_CLIENT_ID"] == ""
    assert data["custom_EXTRA"] == 'unit-$EXTRA-"quoted"'
    assert data["API_KEY"] == environment.api["API_KEY"]
    backups = list((environment.state / "config-backups").glob("*.bak"))
    assert len(backups) == 1 and backups[0].read_text() == original
    assert stat.S_IMODE(backups[0].stat().st_mode) == 0o600
    assert stat.S_IMODE(backups[0].parent.stat().st_mode) == 0o700
    assert result["backup_created"] and result["legacy_sources_preserved"]
    for path, (content, modified) in sources.items():
        assert path.read_bytes() == content and path.stat().st_mtime_ns == modified
    report = json.dumps(result)
    assert "unit-" not in report


def test_missing_canonical_oauth_uses_validated_legacy_as_complete_source(environment):
    write_private(environment.canonical, "CUSTOM_KEEP=unit-extra\n")
    write_private(
        environment.state / "auth/providers.env",
        "AUTH_PUBLIC_BASE_URL=https://unit-login.example.invalid\n"
        "NAVER_CLIENT_ID=unit-naver-id\nNAVER_CLIENT_SECRET='unit-${SECRET}'\n",
    )
    migration.migrate_runtime_settings()
    data = values(environment)
    assert data["NAVER_CLIENT_ID"] == "unit-naver-id"
    assert data["NAVER_CLIENT_SECRET"] == "unit-${SECRET}"
    assert data["CUSTOM_KEEP"] == "unit-extra"
    assert data["KAKAO_CLIENT_ID"] == ""


def test_explicit_blank_canonical_never_reads_or_blends_invalid_legacy(environment):
    write_private(environment.canonical, "KAKAO_CLIENT_ID=\n")
    legacy = write_private(environment.state / "auth/providers.env", "MALFORMED='unterminated\n")
    legacy.chmod(0o644)
    migration.migrate_runtime_settings()
    assert values(environment)["KAKAO_CLIENT_ID"] == ""
    assert values(environment)["GOOGLE_CLIENT_ID"] == ""


@pytest.mark.parametrize("kind", ["permissions", "symlink", "hardlink", "directory", "broken-link"])
def test_rejects_unsafe_canonical_without_reading_runtime_or_changing_source(environment, kind):
    foreign = write_private(environment.root / "foreign.env", "API_KEY=unit-foreign-secret\n")
    if kind == "permissions":
        write_private(environment.canonical, "API_KEY=unit-source-secret\n").chmod(0o644)
    elif kind == "symlink":
        environment.canonical.symlink_to(foreign)
    elif kind == "hardlink":
        os.link(foreign, environment.canonical)
    elif kind == "directory":
        environment.canonical.mkdir(mode=0o700)
    else:
        environment.canonical.symlink_to(environment.root / "missing.env")
    with pytest.raises(RuntimeError) as error:
        migration.migrate_runtime_settings()
    assert "unit-" not in str(error.value)
    assert foreign.read_text() == "API_KEY=unit-foreign-secret\n"
    environment.api_reader.assert_not_called()


@pytest.mark.parametrize("content", [
    "KAKAO_CLIENT_SECRET='unit-unclosed\n", "API_KEY=unit-first\napi_key=unit-second\n",
    "INVALID-NAME=unit-value\n", "KAKAO_CLIENT_ID\n",
])
def test_rejects_invalid_canonical_and_preserves_original(environment, content):
    write_private(environment.canonical, content)
    with pytest.raises(RuntimeError) as error:
        migration.migrate_runtime_settings()
    assert "unit-" not in str(error.value)
    assert environment.canonical.read_text() == content
    environment.api_reader.assert_not_called()


@pytest.mark.parametrize("content", [
    "UNKNOWN_KEY=unit-secret\n", "GOOGLE_CLIENT_SECRET='unit-unclosed\n",
    "KAKAO_CLIENT_ID=unit-one\nkakao_client_id=unit-two\n", "NAVER_CLIENT_ID\n",
])
def test_rejects_invalid_legacy_without_creating_canonical(environment, content):
    legacy = write_private(environment.state / "auth/providers.env", content)
    with pytest.raises(RuntimeError):
        migration.migrate_runtime_settings()
    assert not environment.canonical.exists()
    assert legacy.read_text() == content


def test_rejects_source_parent_symlink_without_changing_other_project(environment):
    other = environment.root / "other-project"
    write_private(other / "providers.env", "KAKAO_CLIENT_SECRET=unit-other-secret\n")
    (environment.state / "auth").symlink_to(other, target_is_directory=True)
    with pytest.raises(RuntimeError):
        migration.migrate_runtime_settings()
    assert not environment.canonical.exists()
    environment.api_reader.assert_not_called()


def test_bedrock_read_failure_is_generic_and_does_not_replace_existing_file(environment, capsys):
    original = "KAKAO_CLIENT_ID=unit-original\n"
    write_private(environment.canonical, original)
    environment.api.update({"AI_PROVIDER": "bedrock", "BEDROCK_AUTH_MODE": "api_key"})
    environment.key_reader.side_effect = RuntimeError("unit-secret-in-upstream-error")
    assert migration.main() == 1
    captured = capsys.readouterr()
    assert captured.out == "" and "unit-secret" not in captured.err
    assert environment.canonical.read_text() == original


@pytest.mark.parametrize("database", [
    {"database": "another_project", "manse_backend": "mysql"},
    {"database": "woonari", "manse_backend": "unsupported"},
])
def test_refuses_another_database_or_backend_before_secret_read(environment, database):
    environment.database.update(database)
    with pytest.raises(RuntimeError):
        migration.migrate_runtime_settings()
    assert not environment.canonical.exists()
    environment.secret_reader.assert_not_called()


def test_atomic_replace_failure_leaves_original_and_cleans_temporary(environment, monkeypatch):
    original = "CUSTOM_KEEP=unit-original\n"
    write_private(environment.canonical, original)
    monkeypatch.setattr(migration.os, "replace", Mock(side_effect=OSError("unit-sensitive-error")))
    with pytest.raises(RuntimeError) as error:
        migration.migrate_runtime_settings()
    assert "unit-sensitive-error" not in str(error.value)
    assert environment.canonical.read_text() == original
    assert not list(environment.canonical.parent.glob(".env-migration-*"))


def test_main_output_contains_only_safe_metadata(environment, capsys):
    environment.api["OPENAI_API_KEY"] = "unit-private-api-key"
    assert migration.main() == 0
    captured = capsys.readouterr()
    assert captured.err == "" and "unit-private" not in captured.out
    report = json.loads(captured.out)
    assert "OPENAI_API_KEY" in report["field_names"]
    assert report["settings_file"] == "python_api/.env"


@pytest.mark.parametrize("host,selected", [
    ("unit.abc.ap-southeast-2.rds.amazonaws.com", "rds-global-bundle.pem"),
    ("unit.proxy-abc.ap-southeast-2.rds.amazonaws.com", "public"),
    ("unit.example.invalid", "mysql-ca.pem"),
])
def test_database_ca_selection_matches_runtime(environment, host, selected):
    if selected != "public":
        path = environment.state / "db" / selected
        path.parent.mkdir()
        path.write_text("unit public certificate")
    else:
        path = environment.ca
    assert migration._database_ca(host) == path


def test_direct_rds_requires_existing_bundle_without_public_ca_fallback(environment):
    with pytest.raises(ValueError):
        migration._database_ca("unit.abc.ap-southeast-2.rds.amazonaws.com")
