"""CR-013: status describes the selected authentication without exposing IDs."""
from fastapi.testclient import TestClient

from app.config import Settings
from app.legacy_catalog import full_catalog
from app.main import create_app


def test_catalog_distinguishes_bearer_settings_from_iam_and_access_success():
    base = dict(ai_key_configured=None, ai_model_configured=True,
                ai_region_configured=True, ai_provider="bedrock")
    iam = full_catalog(**base)["ai_configuration"]
    assert iam["authentication"] == "aws_iam" and iam["key_required"] is False
    for configured in (False, True):
        bearer = full_catalog(**base, ai_auth_mode="api_key",
                              ai_account_configured=configured)["ai_configuration"]
        assert bearer["authentication"] == "bedrock_api_key"
        assert bearer["key_required"] is True and bearer["key_configured"] is None
        assert bearer["configuration_complete"] == configured
        assert bearer["generation_check"] == "not_run"


def test_health_requires_pinned_ai_account_and_never_returns_its_value():
    for account in ("", "111122223333"):
        settings = Settings(
            _env_file=None, ai_provider="bedrock", bedrock_auth_mode="api_key",
            bedrock_model_id="global.anthropic.claude-sonnet-4-6",
            bedrock_region="ap-northeast-2", bedrock_account_id=account,
        )
        with TestClient(create_app(settings)) as client:
            response = client.get("/health")
            health = response.json()
            assert health["bedrock_auth_mode"] == "api_key"
            assert health["ai_configured"] == bool(account)
            assert ("BEDROCK_ACCOUNT_ID" in health["ai_missing_settings"]) == (not account)
            assert "111122223333" not in response.text
            catalog = client.get("/v1/asp-services")
            assert catalog.json()["ai_configuration"]["authentication"] == "bedrock_api_key"
            assert "111122223333" not in catalog.text
