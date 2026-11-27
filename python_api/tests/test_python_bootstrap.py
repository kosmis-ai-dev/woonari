"""CR-025 / T-045: the Python ASGI entrypoint owns deployment settings."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.auth_models import SocialProvider
from app.auth_settings import AuthSettings
from app.auth_store import MySQLAuthStore, SQLiteAuthStore
from app.config import Settings

API_ROOT = Path(__file__).resolve().parents[1]
OAUTH_FIELDS = tuple(
    f"{provider}_client_{kind}"
    for provider in SocialProvider
    for kind in ("id", "secret")
)


@pytest.fixture(autouse=True)
def isolated_process_settings(monkeypatch):
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    monkeypatch.delenv("WOONARI_ENV_FILE", raising=False)


class NoNetworkGateway:
    def __init__(self, events=None):
        self.events = events if events is not None else []

    async def close(self):
        self.events.append("gateway_closed")


class NoAIInterpreter:
    def __init__(self, events=None):
        self.events = events if events is not None else []

    async def interpret(self, result):
        raise AssertionError("Bootstrap must not invoke an AI provider")

    async def close(self):
        self.events.append("interpreter_closed")


class VerifiedMySQLStore(MySQLAuthStore):
    def __init__(self, events, failure=False):
        def no_connection():
            raise AssertionError("Bootstrap fixture must not open a MySQL connection")

        super().__init__(no_connection)
        self.events = events
        self.failure = failure

    def verify(self):
        self.events.append("verify_mysql")
        if self.failure:
            raise RuntimeError("unit-private-database-diagnostic")

    def initialize(self):
        raise AssertionError("Production startup must not issue DDL")


def configured(tmp_path, **changes):
    values = {
        "woonari_env": "production",
        "woonari_db_backend": "mysql",
        "woonari_state_dir": tmp_path / "state",
        "woonari_db_host": "mysql.example.invalid",
        "woonari_db_user": "unit-db-user",
        "woonari_db_password": "unit-private-db-password",
        "auth_public_base_url": "https://api.example.invalid",
        **{field: f"unit-private-{field}" for field in OAUTH_FIELDS},
    }
    return Settings(_env_file=None, **(values | changes))


def test_python_settings_reach_auth_service_and_public_provider_status(tmp_path):
    settings = configured(tmp_path, woonari_env="development", woonari_db_backend="sqlite")
    application = main.create_app(
        settings,
        auth_store=SQLiteAuthStore(tmp_path / "members.sqlite3"),
        oauth_gateway=NoNetworkGateway(),
        interpreter_factory=lambda _: NoAIInterpreter(),
    )
    with TestClient(application) as client:
        response = client.get("/v1/auth/providers")
        assert response.status_code == 200
        providers = response.json()["items"]
        assert len(providers) == 3
        assert all(item["configured"] for item in providers)
        assert all(item["callback_url"].startswith("https://api.example.invalid/") for item in providers)
        assert "unit-private" not in response.text
        assert application.state.auth_service.settings.credentials(SocialProvider.kakao) == (
            "unit-private-kakao_client_id", "unit-private-kakao_client_secret"
        )


def _run_python(code, cwd, **environment):
    # The subprocess cannot inherit another project's model or provider keys.
    result = subprocess.run(
        [sys.executable, "-B", "-I", "-c", f"import sys; sys.path.insert(0, {str(API_ROOT)!r})\n" + code],
        cwd=cwd,
        env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1", **environment},
        text=True, capture_output=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "bootstrap-ok"
    assert result.stderr == ""


def test_raw_uvicorn_target_import_does_not_read_settings_or_create_state(tmp_path):
    _run_python(
        """
import app.config as config
def forbidden():
    raise AssertionError('ASGI module import must not read configuration')
config.get_settings = forbidden
from uvicorn.importer import import_from_string
target = import_from_string('app.main:app')
assert target.application is None
print('bootstrap-ok')
""",
        tmp_path,
        WOONARI_ENV_FILE=str(tmp_path / "missing-private.env"),
        WOONARI_ENV="production",
        WOONARI_STATE_DIR=str(tmp_path / "must-not-create"),
    )
    assert not (tmp_path / "must-not-create").exists()


def test_raw_uvicorn_target_reads_explicit_file_from_foreign_working_directory(tmp_path):
    selected = tmp_path / "deployed.env"
    content = ["WOONARI_ENV=development", f"WOONARI_STATE_DIR={tmp_path / 'state'}"]
    content += ["AUTH_PUBLIC_BASE_URL=https://api.example.invalid"]
    content += ["AI_PROVIDER=bedrock", "AWS_BEARER_TOKEN_BEDROCK=unit-file-bedrock-token"]
    content += [f"{field.upper()}=unit-file-{field}" for field in OAUTH_FIELDS]
    selected.write_text("\n".join(content) + "\n")
    selected.chmod(0o600)
    _run_python(
        """
from fastapi.testclient import TestClient
from uvicorn.importer import import_from_string
import app.main as main
import app.auth_providers as providers
class NoNetworkGateway:
    async def close(self):
        pass
class NoAI:
    async def close(self):
        pass
providers.SocialOAuthGateway = NoNetworkGateway
def interpreter(settings, **kwargs):
    assert settings.ai_provider == 'bedrock'
    assert settings.aws_bearer_token_bedrock.get_secret_value() == 'unit-file-bedrock-token'
    return NoAI()
main._default_interpreter = interpreter
target = import_from_string('app.main:app')
assert target.application is None
with TestClient(target) as client:
    response = client.get('/v1/auth/providers')
    assert response.status_code == 200
    assert all(item['configured'] for item in response.json()['items'])
    assert 'unit-file' not in response.text and 'unit-process' not in response.text
    auth = target.application.state.auth_service.settings
    assert auth.kakao_client_id.get_secret_value() == 'unit-process-kakao'
    assert auth.kakao_client_secret.get_secret_value() == 'unit-file-kakao_client_secret'
print('bootstrap-ok')
""",
        tmp_path,
        WOONARI_ENV_FILE=str(selected), KAKAO_CLIENT_ID="unit-process-kakao",
    )
    # Provider status performs no model transmission or member database writes.
    assert not (tmp_path / "state").exists()


@pytest.mark.parametrize("field", OAUTH_FIELDS)
def test_production_missing_provider_secret_fails_before_state_or_dependencies(tmp_path, monkeypatch, field):
    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid production settings must fail before dependencies")

    monkeypatch.setattr(main, "build_mysql_runtime", forbidden)
    with pytest.raises(RuntimeError) as caught:
        main.create_app(configured(tmp_path, **{field: ""}), interpreter_factory=forbidden)
    assert "unit-private" not in str(caught.value)
    assert not (tmp_path / "state").exists()


@pytest.mark.parametrize("change", [
    {"woonari_db_backend": "sqlite"},
    {"woonari_state_dir": None},
    {"woonari_state_dir": Path("relative-state")},
    {"woonari_db_host": ""},
    {"woonari_db_user": ""},
    {"woonari_db_password": ""},
    {"woonari_db_name": "other-project"},
])
def test_production_requires_explicit_woonari_mysql_and_state(tmp_path, monkeypatch, change):
    def forbidden(*args, **kwargs):
        raise AssertionError("Incomplete database settings must not connect")

    monkeypatch.setattr(main, "build_mysql_runtime", forbidden)
    with pytest.raises(RuntimeError):
        main.create_app(configured(tmp_path, **change), interpreter_factory=forbidden)
    assert not (tmp_path / "state").exists()


def test_explicit_empty_auth_settings_cannot_bypass_production_validation(tmp_path):
    with pytest.raises(RuntimeError):
        main.create_app(configured(tmp_path), auth_settings=AuthSettings())
    assert not (tmp_path / "state").exists()


def test_production_rejects_injected_sqlite_without_creating_state(tmp_path):
    with pytest.raises(RuntimeError, match="MySQL"):
        main.create_app(configured(tmp_path), auth_store=SQLiteAuthStore(tmp_path / "forbidden.sqlite3"))
    assert not (tmp_path / "forbidden.sqlite3").exists()
    assert not (tmp_path / "state").exists()


def test_production_verifies_mysql_before_ai_and_preserves_durable_state(tmp_path):
    events = []
    store = VerifiedMySQLStore(events)
    gateway = NoNetworkGateway(events)

    def interpreter_factory(settings):
        events.append("create_interpreter")
        return NoAIInterpreter(events)

    application = main.create_app(
        configured(tmp_path), auth_store=store, oauth_gateway=gateway,
        interpreter_factory=interpreter_factory,
    )
    state = tmp_path / "state"
    marker = state / "existing-ledger-marker"
    marker.write_bytes(b"preserve")
    assert events == []
    assert application.state.ai_quota.path == state / "ai/usage.sqlite3"
    with TestClient(application) as client:
        assert events == ["verify_mysql", "create_interpreter"]
        assert client.get("/v1/auth/providers").status_code == 200
    assert events == ["verify_mysql", "create_interpreter", "interpreter_closed", "gateway_closed"]
    assert marker.read_bytes() == b"preserve"
    assert set(state.iterdir()) == {marker}


def test_development_explicit_mysql_verifies_store_before_ai_without_requiring_oauth(tmp_path):
    events = []

    def interpreter_factory(settings):
        events.append("create_interpreter")
        return NoAIInterpreter(events)

    application = main.create_app(
        configured(tmp_path, woonari_env="development", **{field: "" for field in OAUTH_FIELDS}),
        auth_store=VerifiedMySQLStore(events), oauth_gateway=NoNetworkGateway(events),
        interpreter_factory=interpreter_factory,
    )
    assert events == []
    with TestClient(application) as client:
        assert events == ["verify_mysql", "create_interpreter"]
        assert all(not item["configured"] for item in client.get("/v1/auth/providers").json()["items"])
    assert events == ["verify_mysql", "create_interpreter", "interpreter_closed", "gateway_closed"]


def test_production_schema_failure_stops_ai_and_closes_gateway(tmp_path):
    events = []

    def forbidden(settings):
        raise AssertionError("Unavailable member schema must stop AI initialization")

    application = main.create_app(
        configured(tmp_path), auth_store=VerifiedMySQLStore(events, failure=True),
        oauth_gateway=NoNetworkGateway(events), interpreter_factory=forbidden,
    )
    with pytest.raises(RuntimeError) as caught, TestClient(application):
        pass
    assert "unit-private-database-diagnostic" not in str(caught.value)
    assert events == ["verify_mysql", "gateway_closed"]


def test_interpreter_initialization_failure_still_closes_gateway(tmp_path):
    events = []

    def unavailable(settings):
        events.append("create_interpreter")
        raise RuntimeError("unit-interpreter-unavailable")

    application = main.create_app(
        configured(tmp_path), auth_store=VerifiedMySQLStore(events),
        oauth_gateway=NoNetworkGateway(events), interpreter_factory=unavailable,
    )
    with pytest.raises(RuntimeError, match="unit-interpreter-unavailable"), TestClient(application):
        pass
    assert events == ["verify_mysql", "create_interpreter", "gateway_closed"]
