"""CR-015: make restoration and verified service lookup distinct in guides."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import app.service_engine as engine
import app.source_archive as archive
import app.source_catalog as catalog
from app.ai_quota import DailyAIQuota
from app.config import Settings
from app.legacy_catalog import services
from app.main import create_app


def registry(tmp_path, monkeypatch):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps({"format": "woonari.fortune-archive.v1", "tables": [
        {"source_table": "tbPreLife", "row_count": 114},
        {"source_table": "TB_FlowerLuck", "row_count": 366},
        {"source_table": "TB_yearLuck", "row_count": 7000},
        {"source_table": "yearfortune del", "row_count": 0},
    ]}))
    monkeypatch.setattr(catalog, "REGISTRY_PATH", path)
    monkeypatch.setattr(catalog, "_cached", None)
    return path


def test_exact_verified_lookup_and_unverified_annual_candidates(tmp_path, monkeypatch):
    registry(tmp_path, monkeypatch)
    past = catalog.service_archive_status({"dependencies": [{"name": "tbPreLife"}]})
    assert past["tables"] == [{"requested_table": "tbPreLife", "source_table": "tbPreLife",
                               "row_count": 114, "status": "restored_definition",
                               "lookup_mapping": "verified"}]
    assert not past["actual_connection_checked"]
    annual = catalog.service_archive_status({"api_kind": "yearly"})
    assert annual["tables"] == []
    assert annual["required_for_execution"] is False
    assert annual["basis"] == "annual_saju_ai"
    assert annual["status_path"] == "/v1/restored-data"


def test_missing_registry_has_no_false_restored_claim(tmp_path, monkeypatch):
    monkeypatch.setattr(catalog, "REGISTRY_PATH", tmp_path / "absent.json")
    monkeypatch.setattr(catalog, "_cached", None)
    status = catalog.service_archive_status({"api_kind": "compatibility"})
    assert status["tables"][0]["status"] == "not_found_exact"


def test_empty_source_is_shown_as_empty_and_registry_refreshes(tmp_path, monkeypatch):
    path = registry(tmp_path, monkeypatch)
    status = catalog.service_archive_status({"dependencies": [{"name": "yearfortune del"}]})
    assert status["tables"][0]["status"] == "restored_empty"
    path.write_text('{"format":"invalid", "tables":[]}')
    assert catalog.registry_snapshot()["tables"] == []
    path.write_text('[]')
    assert catalog.registry_snapshot()["tables"] == []


def test_source_status_endpoint_authorization_and_no_model_call(tmp_path, monkeypatch):
    monkeypatch.setattr(archive, "_factory", None)
    interpreter = SimpleNamespace(close=AsyncMock(), interpret=AsyncMock())
    application = create_app(
        Settings(_env_file=None, api_key="synthetic-api"),
        interpreter_factory=lambda _: interpreter,
        ai_quota=DailyAIQuota(tmp_path / "usage.sqlite3", private_root=tmp_path),
    )
    with TestClient(application) as client:
        assert client.get("/v1/source-data").status_code == 404
        headers = {"X-API-Key": "synthetic-api"}
        response = client.get("/v1/source-data", headers=headers)
        assert response.status_code == 404
        assert "/v1/source-data" not in application.openapi()["paths"]
        assert client.get("/v1/ai-usage", headers=headers).json()["used"] == 0
    interpreter.interpret.assert_not_called()


@pytest.mark.parametrize("service_id", ["flowerluck", "jewelryluck"])
def test_source_classification_service_metadata_requires_archive_configuration(service_id, monkeypatch):
    monkeypatch.setattr(engine, "is_source_archive_configured", lambda: False)
    assert engine.service_metadata(service_id)["status"] == "source_required"
    monkeypatch.setattr(engine, "is_source_archive_configured", lambda: True)
    metadata = engine.service_metadata(service_id)
    assert metadata["status"] == "ready"
    assert metadata["source_archive"]["actual_connection_checked"] is False


def test_catalog_does_not_keep_resolved_identity_missing_issue(monkeypatch):
    monkeypatch.setattr(archive, "_factory", lambda: None)
    by_id = {item["id"]: item for item in services()}
    for service_id, issue_code in (("flowerluck", "birth_flower_identity_missing"),
                                   ("jewelryluck", "birth_stone_identity_missing")):
        item = by_id[service_id]
        assert item["status"] == "ready"
        assert item["test_path"] == f"/v1/un/{service_id}"
        assert not any(issue["code"] == issue_code for issue in item["issues"])
    assert any("lmyMonth" in note for note in by_id["jewelryluck"]["review_notes"])
