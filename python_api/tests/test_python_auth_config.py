"""CR-025 / T-045: package-owned settings and safe social source selection."""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

import app.auth_settings as auth
import app.config as configuration
from app.auth_models import SocialProvider
from app.auth_settings import (
    AuthSettings,
    auth_settings_from_python,
    load_local_auth_settings,
    local_auth_source,
    validate_production_auth,
)
from app.config import Settings, get_settings


def write_env(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o600)
    return path


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    names = {name.lower() for name in Settings.model_fields} | {"woonari_env_file"}
    for key in list(os.environ):
        if key.lower() in names:
            monkeypatch.delenv(key)
    canonical = tmp_path / "python_api/.env"
    legacy = tmp_path / ".local/woonari/auth/providers.env"
    monkeypatch.setattr(configuration, "DEFAULT_ENV_FILE", canonical)
    monkeypatch.setattr(auth, "PROVIDERS_FILE", legacy)
    return canonical, legacy


def complete_credentials():
    return {
        f"{provider}_client_{kind}": f"unit-{provider}-{kind}"
        for provider in SocialProvider for kind in ("id", "secret")
    }


def test_python_file_and_process_share_settings_and_process_wins(isolated_environment, monkeypatch):
    canonical, _ = isolated_environment
    write_env(canonical, "KAKAO_CLIENT_ID=file-id\nKAKAO_CLIENT_SECRET=file-secret\nAUTH_PUBLIC_BASE_URL=https://login.example.invalid\n")
    monkeypatch.setenv("KAKAO_CLIENT_SECRET", "process-secret")
    value = get_settings()
    result = auth_settings_from_python(value)
    assert result.configured(SocialProvider.kakao)
    assert result.kakao_client_id.get_secret_value() == "file-id"
    assert result.kakao_client_secret.get_secret_value() == "process-secret"
    assert result.callback_url(SocialProvider.kakao) == "https://login.example.invalid/v1/auth/kakao/callback"
    assert "process-secret" not in repr(value)
    assert "process-secret" not in repr(result)


def test_cwd_env_is_never_discovered(isolated_environment, monkeypatch, tmp_path):
    foreign = tmp_path / "another-project"
    write_env(foreign / ".env", "KAKAO_CLIENT_ID=foreign-id\nKAKAO_CLIENT_SECRET=foreign-secret\n")
    monkeypatch.chdir(foreign)
    assert not auth_settings_from_python(get_settings()).configured(SocialProvider.kakao)


def test_explicit_absolute_env_path_overrides_canonical(isolated_environment, monkeypatch, tmp_path):
    canonical, _ = isolated_environment
    write_env(canonical, "KAKAO_CLIENT_ID=canonical-id\n")
    selected = write_env(tmp_path / "mounted/runtime.env", "KAKAO_CLIENT_ID=selected-id\nKAKAO_CLIENT_SECRET=selected-secret\n")
    monkeypatch.setenv("WOONARI_ENV_FILE", str(selected))
    assert get_settings().kakao_client_id.get_secret_value() == "selected-id"


@pytest.mark.parametrize("value", ["", "relative.env", "../another.env"])
def test_explicit_empty_or_relative_env_file_fails_without_values(monkeypatch, value):
    monkeypatch.setenv("WOONARI_ENV_FILE", value)
    with pytest.raises(RuntimeError, match="절대 경로"):
        get_settings()


def test_explicit_missing_file_is_not_ignored(monkeypatch, tmp_path):
    monkeypatch.setenv("WOONARI_ENV_FILE", str(tmp_path / "missing.env"))
    with pytest.raises(RuntimeError, match="환경설정 파일"):
        get_settings()


@pytest.mark.parametrize("kind", ["permissions", "symlink", "directory"])
def test_selected_file_is_private_regular_owned_file(isolated_environment, kind):
    canonical, _ = isolated_environment
    if kind == "directory":
        canonical.mkdir(parents=True)
    else:
        write_env(canonical, "KAKAO_CLIENT_ID=unit-id\n")
        if kind == "permissions":
            canonical.chmod(0o644)
        else:
            target = canonical.with_name("real.env")
            canonical.rename(target)
            canonical.symlink_to(target)
    with pytest.raises(RuntimeError, match="환경설정 파일"):
        get_settings()


def test_wrong_owner_is_rejected_without_contents(isolated_environment, monkeypatch):
    canonical, _ = isolated_environment
    write_env(canonical, "KAKAO_CLIENT_SECRET=must-not-print\n")
    monkeypatch.setattr(configuration.os, "getuid", lambda: canonical.stat().st_uid + 1)
    with pytest.raises(RuntimeError) as failure:
        get_settings()
    assert "must-not-print" not in str(failure.value)


@pytest.mark.parametrize("text", [
    "KAKAO_CLIENT_SECRET='unterminated-private-value\n",
    "KAKAO_CLIENT_ID=first\nkakao_client_id=second\n",
    "WOONARI_DB_PORT=not-a-port-private-value\n"
])
def test_invalid_file_and_settings_errors_do_not_echo_values(isolated_environment, text):
    canonical, _ = isolated_environment
    write_env(canonical, text)
    with pytest.raises(RuntimeError) as failure:
        get_settings()
    assert "unterminated-private-value" not in str(failure.value)
    assert "not-a-port-private-value" not in str(failure.value)
    assert "first" not in str(failure.value)


def test_explicit_env_file_none_preserves_constructor_isolation(isolated_environment, monkeypatch):
    canonical, _ = isolated_environment
    write_env(canonical, "KAKAO_CLIENT_ID=file-id\nKAKAO_CLIENT_SECRET=file-secret\n")
    assert Settings(_env_file=None).kakao_client_id.get_secret_value() == ""
    monkeypatch.setenv("KAKAO_CLIENT_ID", "process-id")
    assert Settings(_env_file=None).kakao_client_id.get_secret_value() == "process-id"


def test_literal_dollar_credentials_never_expand(isolated_environment, monkeypatch):
    canonical, _ = isolated_environment
    write_env(canonical, "KAKAO_CLIENT_ID=unit-id\nKAKAO_CLIENT_SECRET='${EXTERNAL_SECRET}-$EXTERNAL_SECRET'\n")
    monkeypatch.setenv("EXTERNAL_SECRET", "ambient-value-must-not-expand")
    value = "${EXTERNAL_SECRET}-$EXTERNAL_SECRET"
    assert get_settings().kakao_client_secret.get_secret_value() == value
    assert load_local_auth_settings().kakao_client_secret.get_secret_value() == value


def test_explicit_settings_values_win_and_new_optional_empty_paths_are_none(tmp_path):
    path = write_env(tmp_path / "fixture.env", "KAKAO_CLIENT_ID=file-id\n")
    value = Settings(_env_file=path, kakao_client_id="explicit-id", woonari_state_dir="", woonari_db_ca_file="")
    assert value.kakao_client_id.get_secret_value() == "explicit-id"
    assert value.woonari_state_dir is None and value.woonari_db_ca_file is None


def test_local_loader_falls_back_to_legacy_as_one_source(isolated_environment, monkeypatch):
    _, legacy = isolated_environment
    write_env(legacy, "KAKAO_CLIENT_ID=legacy-id\nKAKAO_CLIENT_SECRET=legacy-secret\n")
    value = load_local_auth_settings()
    assert value.kakao_client_secret.get_secret_value() == "legacy-secret"
    assert local_auth_source() == str(legacy)
    # The legacy file-specific API continues ignoring ambient OAuth settings.
    monkeypatch.setenv("KAKAO_CLIENT_SECRET", "ambient-secret")
    assert auth.load_auth_settings(legacy).kakao_client_secret.get_secret_value() == "legacy-secret"


def test_canonical_source_never_merges_legacy_credentials(isolated_environment):
    canonical, legacy = isolated_environment
    write_env(legacy, "KAKAO_CLIENT_ID=legacy-id\nKAKAO_CLIENT_SECRET=legacy-secret\nGOOGLE_CLIENT_ID=legacy-google-id\nGOOGLE_CLIENT_SECRET=legacy-google-secret\n")
    write_env(canonical, "KAKAO_CLIENT_ID=canonical-id\nKAKAO_CLIENT_SECRET=\n")
    value = load_local_auth_settings()
    assert value.kakao_client_id.get_secret_value() == "canonical-id"
    assert value.kakao_client_secret.get_secret_value() == ""
    assert not value.configured(SocialProvider.google)
    assert local_auth_source() == str(canonical)


def test_local_loader_ignores_ai_and_database_validation(isolated_environment):
    canonical, _ = isolated_environment
    write_env(canonical, "AI_TIMEOUT_SECONDS=invalid-unused-value\nWOONARI_DB_PORT=invalid-unused-port\nKAKAO_CLIENT_ID=unit-id\nKAKAO_CLIENT_SECRET=unit-secret\n")
    assert load_local_auth_settings().configured(SocialProvider.kakao)


def test_local_loader_accepts_missing_canonical_for_legacy_bootstrap(tmp_path):
    canonical = tmp_path / "not-created.env"
    legacy = write_env(tmp_path / "legacy.env", "KAKAO_CLIENT_ID=legacy-id\nKAKAO_CLIENT_SECRET=legacy-secret\n")
    value = load_local_auth_settings(python_env_file=canonical, legacy_file=legacy)
    assert value.kakao_client_id.get_secret_value() == "legacy-id"
    assert local_auth_source(python_env_file=canonical, legacy_file=legacy) == str(legacy)
    assert not canonical.exists()


def test_local_source_metadata_shows_environment_without_secret_values(monkeypatch):
    monkeypatch.setenv("KAKAO_CLIENT_ID", "sensitive-client-id")
    monkeypatch.setenv("KAKAO_CLIENT_SECRET", "sensitive-client-secret")
    assert local_auth_source() == "environment"


@pytest.mark.parametrize("changes", [
    {"auth_public_base_url": "http://127.0.0.1:9090"},
    {"auth_public_base_url": "https://localhost"},
    {"auth_public_base_url": "https://127.0.0.1"},
    {"auth_public_base_url": "https://[::1]"},
    {"kakao_client_secret": ""},
    {"google_client_id": ""},
    {"naver_client_secret": ""}
])
def test_production_auth_requires_all_keys_and_public_https(changes):
    values = complete_credentials() | {"auth_public_base_url": "https://api.example.invalid"} | changes
    settings = Settings(_env_file=None, woonari_env="production", **values)
    result = auth_settings_from_python(settings)
    with pytest.raises(RuntimeError) as failure:
        validate_production_auth(settings, result)
    for value in complete_credentials().values():
        assert value not in str(failure.value)


def test_production_https_and_complete_credentials_are_accepted():
    settings = Settings(
        _env_file=None, woonari_env="production", auth_public_base_url="HTTPS://api.example.invalid",
        **complete_credentials()
    )
    auth_settings = auth_settings_from_python(settings)
    validate_production_auth(settings, auth_settings)
    assert auth_settings.secure_cookie


def test_development_can_keep_social_login_unconfigured():
    settings = Settings(_env_file=None)
    value = auth_settings_from_python(settings)
    validate_production_auth(settings, value)
    assert all(not value.configured(provider) for provider in SocialProvider)


def test_auth_projection_errors_and_settings_validation_hide_inputs():
    settings = Settings(_env_file=None, kakao_client_secret="sensitive secret has spaces")
    with pytest.raises(RuntimeError) as failure:
        auth_settings_from_python(settings)
    assert "sensitive secret" not in str(failure.value)
    with pytest.raises(ValidationError) as failure:
        AuthSettings(kakao_client_secret="another private secret")
    assert "another private secret" not in str(failure.value)


def test_python_settings_own_all_provider_values_without_other_secret_projection():
    value = Settings(
        _env_file=None, woonari_env="test", woonari_db_password="database-private-value",
        openai_api_key="ai-private-value", aws_bearer_token_bedrock="bedrock-private-value",
        **complete_credentials()
    )
    auth_value = auth_settings_from_python(value)
    assert set(AuthSettings.model_fields) == {
        "auth_public_base_url", "kakao_client_id", "kakao_client_secret", "google_client_id",
        "google_client_secret", "naver_client_id", "naver_client_secret"
    }
    assert "database-private-value" not in repr(auth_value)
    assert "ai-private-value" not in repr(auth_value)
    assert "bedrock-private-value" not in repr(auth_value)
    assert "bedrock-private-value" not in repr(value)


def test_bedrock_key_and_mysql_selection_are_loaded_from_python_file(isolated_environment):
    canonical, _ = isolated_environment
    write_env(canonical, "AWS_BEARER_TOKEN_BEDROCK='${LITERAL_BEDROCK_KEY}'\nWOONARI_DB_BACKEND=mysql\n")
    value = get_settings()
    assert value.aws_bearer_token_bedrock.get_secret_value() == "${LITERAL_BEDROCK_KEY}"
    assert value.woonari_db_backend == "mysql"


def test_invalid_database_backend_fails_without_value(isolated_environment):
    canonical, _ = isolated_environment
    write_env(canonical, "WOONARI_DB_BACKEND=private-invalid-backend\n")
    with pytest.raises(RuntimeError) as failure:
        get_settings()
    assert "private-invalid-backend" not in str(failure.value)
