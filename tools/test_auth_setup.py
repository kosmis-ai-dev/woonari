"""CR-022 / T-042: private setup and value-free social auth operations."""

import importlib.machinery
import importlib.util
import json
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import auth_setup as setup
import isolated_db
import project_context
import pytest
from app.errors import DomainError


@pytest.fixture
def providers_file(tmp_path, monkeypatch):
    monkeypatch.setattr(project_context, "ROOT", tmp_path)
    path = tmp_path / ".local/woonari/auth/providers.env"
    monkeypatch.setattr(setup, "PROVIDERS_FILE", path)
    return path


def test_init_creates_private_template_and_reports_unverified_providers(providers_file, capsys):
    assert setup.main(["init"]) == 0
    output = capsys.readouterr()
    assert output.err == ""
    value = json.loads(output.out)
    assert value["settings_file"] == ".local/woonari/auth/providers.env"
    assert {item["provider"] for item in value["providers"]} == {"kakao", "google", "naver"}
    assert all(item["configured"] is False for item in value["providers"])
    assert all(item["actual_login_verified"] is False for item in value["providers"])
    assert "CLIENT_SECRET" not in output.out
    assert providers_file.read_text() == setup.TEMPLATE
    assert stat.S_IMODE(providers_file.stat().st_mode) == 0o600
    assert stat.S_IMODE(providers_file.parent.stat().st_mode) == 0o700


def test_init_preserves_existing_credentials_and_status_never_prints_them(providers_file, capsys):
    setup.initialize_settings()
    content = "KAKAO_CLIENT_ID=unit-private-id\nKAKAO_CLIENT_SECRET=unit-private-secret\n"
    providers_file.write_text(content)
    before = providers_file.stat().st_mtime_ns
    assert setup.main(["init"]) == 0
    assert providers_file.read_text() == content
    assert providers_file.stat().st_mtime_ns == before
    assert setup.main(["status"]) == 0
    output = capsys.readouterr().out
    assert "unit-private-id" not in output and "unit-private-secret" not in output
    values = setup.status()["providers"]
    assert next(item for item in values if item["provider"] == "kakao")["configured"] is True
    assert all(item["actual_login_verified"] is False for item in values)


def test_status_is_read_only_and_does_not_fall_back_to_environment(providers_file, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "unit-other-project-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "unit-other-project-secret")
    connector = Mock()
    monkeypatch.setattr(isolated_db, "mysql_connector", connector)
    value = setup.status()
    assert not providers_file.exists()
    assert all(not item["configured"] for item in value["providers"])
    connector.assert_not_called()


def test_init_refuses_insecure_existing_file_without_replacing_it(providers_file):
    setup.initialize_settings()
    content = "KAKAO_CLIENT_SECRET=unit-existing-sensitive-value\n"
    providers_file.write_text(content)
    providers_file.chmod(0o644)
    with pytest.raises(DomainError) as error:
        setup.initialize_settings()
    assert error.value.code == "auth_configuration_invalid"
    assert "unit-existing-sensitive-value" not in str(error.value)
    assert providers_file.read_text() == content
    assert stat.S_IMODE(providers_file.stat().st_mode) == 0o644


def test_init_refuses_symlink_without_touching_target(providers_file, tmp_path):
    project_context.private_dir(providers_file.parent)
    target = tmp_path / "other-project-provider.env"
    target.write_text("KAKAO_CLIENT_SECRET=unit-foreign-value\n")
    target.chmod(0o600)
    providers_file.symlink_to(target)
    with pytest.raises(DomainError):
        setup.initialize_settings()
    assert target.read_text() == "KAKAO_CLIENT_SECRET=unit-foreign-value\n"
    assert providers_file.is_symlink()


@pytest.mark.parametrize("configuration", [
    {"database": "different_project", "manse_backend": "mysql"},
    {"database": "", "manse_backend": "mysql"},
    {"database": "woonari", "manse_backend": "sqlite"}
])
def test_database_setup_refuses_any_fallback_or_other_database(configuration, monkeypatch):
    connector = Mock()
    store_factory = Mock()
    monkeypatch.setattr(isolated_db, "database_config", lambda: configuration)
    monkeypatch.setattr(isolated_db, "mysql_connector", connector)
    monkeypatch.setattr(setup, "MySQLAuthStore", store_factory)
    with pytest.raises(RuntimeError, match="woonari MySQL"):
        setup.initialize_database()
    connector.assert_not_called()
    store_factory.assert_not_called()


def test_database_setup_uses_only_project_woonari_connector_and_value_free_counts(monkeypatch, capsys):
    monkeypatch.setattr(isolated_db, "database_config", lambda: {
        "database": "woonari", "manse_backend": "mysql"
    })
    connection_factory = object()
    connector = Mock(return_value=connection_factory)
    monkeypatch.setattr(isolated_db, "mysql_connector", connector)
    counts = {"woonari_auth_users": 0, "woonari_auth_identities": 0, "woonari_auth_sessions": 0}
    store = Mock()
    store.counts.return_value = counts
    store_factory = Mock(return_value=store)
    monkeypatch.setattr(setup, "MySQLAuthStore", store_factory)
    assert setup.main(["init-db"]) == 0
    connector.assert_called_once_with("woonari")
    store_factory.assert_called_once_with(connection_factory)
    store.initialize.assert_called_once_with()
    store.counts.assert_called_once_with()
    value = json.loads(capsys.readouterr().out)
    assert value == {"database": "woonari", "authentication_tables": counts}


def test_database_schema_failure_is_not_replaced_with_a_local_store(monkeypatch):
    monkeypatch.setattr(isolated_db, "database_config", lambda: {
        "database": "woonari", "manse_backend": "mysql"
    })
    monkeypatch.setattr(isolated_db, "mysql_connector", Mock(return_value=object()))
    store = Mock()
    store.initialize.side_effect = DomainError("auth_storage_unavailable", "인증 저장소를 확인하세요.", 503)
    monkeypatch.setattr(setup, "MySQLAuthStore", Mock(return_value=store))
    with pytest.raises(DomainError) as error:
        setup.initialize_database()
    assert error.value.status == 503
    store.counts.assert_not_called()


def _cli_module():
    source = Path(__file__).resolve().parents[1] / "woonari"
    loader = importlib.machinery.SourceFileLoader("woonari_auth_entry_under_test", str(source))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


@pytest.mark.parametrize("arguments, expected", [
    (["auth", "init"], ["init"]),
    (["auth", "status"], ["status"]),
    (["db", "init-auth"], ["init-db"])
])
def test_entrypoint_uses_project_python_isolation_and_clean_environment(arguments, expected, tmp_path, monkeypatch):
    module = _cli_module()
    monkeypatch.setattr(project_context, "ROOT", tmp_path)
    private_python = tmp_path / "python_api/.venv/bin/python"
    private_python.parent.mkdir(parents=True)
    private_python.touch()
    clean = {"PATH": "/unit/project-only/path"}
    monkeypatch.setattr(project_context, "clean_env", lambda: clean)
    runner = Mock(return_value=subprocess.CompletedProcess([], 7))
    monkeypatch.setattr(subprocess, "run", runner)
    monkeypatch.setattr(sys, "argv", ["woonari", *arguments])
    assert module.main() == 7
    runner.assert_called_once_with(
        [str(private_python), "-I", str(tmp_path / "tools/auth_setup.py"), *expected],
        cwd=tmp_path, env=clean, check=False
    )


@pytest.mark.parametrize("arguments", [["auth"], ["auth", "init-db"], ["auth", "status", "--profile", "default"]])
def test_entrypoint_does_not_accept_arbitrary_auth_arguments(arguments, monkeypatch):
    module = _cli_module()
    runner = Mock()
    monkeypatch.setattr(subprocess, "run", runner)
    monkeypatch.setattr(sys, "argv", ["woonari", *arguments])
    with pytest.raises(RuntimeError, match="auth init\\|status"):
        module.main()
    runner.assert_not_called()
