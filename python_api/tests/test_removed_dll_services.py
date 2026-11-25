"""CR-019 / T-039: removed DLL services stay unavailable on every public surface."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app import legacy_relationships
from app.ai_quota import DailyAIQuota
from app.config import Settings
from app.fortunes import catalog
from app.legacy_catalog import services
from app.main import create_app
from app.models import FortuneKind, FortuneRequest
from app.service_engine import service_catalog

RAW_CATALOG = Path(__file__).resolve().parents[1] / "app/data/legacy_services.json"
DLL_SERVICES = {
    "animalluck", "basicluck", "carrerluck", "gyukgukluck", "idealluck", "loveandluck",
    "makingloveluck", "originalwedluck", "perfumeluck", "sonluck", "adultluck-sexluck"
}
DUPLICATE_MENUS = {"menu-im34", "menu-im62", "menu-im70", "menu-im71"}
REMOVED = DLL_SERVICES | DUPLICATE_MENUS
REMOVED_MENU_CODES = {"IM9", "IM14", "IM34", "IM62", "IM70", "IM71"}
BIRTH = {"year": 1974, "month": 3, "day": 2, "hour": 8, "minute": 30, "gender": "male"}


@pytest.fixture(scope="module")
def api(tmp_path_factory):
    private = tmp_path_factory.mktemp("dll-retirement")
    quota = DailyAIQuota(private / "ai/usage.sqlite3", private_root=private, limit=100)
    fake = SimpleNamespace(
        name="retirement-test", model="never-call",
        interpret=AsyncMock(side_effect=AssertionError("removed services must not call AI")),
        close=AsyncMock()
    )
    app = create_app(
        Settings(_env_file=None, api_key=None, openai_api_key=None, openai_model=""),
        interpreter_factory=lambda _: fake, ai_quota=quota
    )
    with TestClient(app) as client:
        yield client, app.openapi(), fake


def test_dll_removal_does_not_erase_the_frozen_source_audit():
    assert hashlib.sha256(RAW_CATALOG.read_bytes()).hexdigest() == "956b558c755d600aee12b26f9e4e54a447a047882cbd2fa61d1816353d9d6110"
    original = json.loads(RAW_CATALOG.read_text())
    assert len(original["items"]) == 306
    original_dll = {item["id"] for item in original["items"] if any(
        issue["code"] in {"opaque_com_rule", "nhcp5_calculation_missing"} for issue in item["issues"]
    )}
    assert original_dll == DLL_SERVICES
    original_ids = {item["id"] for item in original["items"]}
    active_ids = {item["id"] for item in services()}
    assert original_ids - active_ids == REMOVED
    assert not active_ids - original_ids


def test_removed_services_are_absent_from_all_lists_and_menu_edges(api):
    client, _, _ = api
    data = client.get("/v1/asp-services").json()
    runtime = client.get("/v1/un-services").json()
    assert runtime["count"] == len(runtime["items"]) == 291
    assert data["summary"]["records"] == len(data["items"]) == 291
    assert {item["id"] for item in services()} == {item["id"] for item in service_catalog()}
    assert len(data["menu_map"]) == 84
    assert not REMOVED_MENU_CODES & {item["content_code"] for item in data["menu_map"]}
    for item in data["items"] + runtime["items"]:
        assert item["id"] not in REMOVED
        assert item["parent_id"] not in REMOVED
        assert not REMOVED & set(item["children"])
        assert not REMOVED & set(item["related_service_ids"])
        assert not REMOVED_MENU_CODES & set(item["menu_codes"])
        assert not any(issue["code"] in {"opaque_com_rule", "nhcp5_calculation_missing"} for issue in item["issues"])
    assert not REMOVED & {item["catalog_id"] for item in data["menu_map"]}


def test_parent_and_other_fortunes_are_preserved(api):
    client, _, _ = api
    original = {item["id"]: item for item in json.loads(RAW_CATALOG.read_text())["items"]}
    active = {item["id"]: item for item in services()}
    assert set(active["adultluck"]["children"]) == set(original["adultluck"]["children"]) - {"adultluck-sexluck"}
    assert len(active["adultluck"]["children"]) == 7
    issue = active["adultluck"]["issues"][0]
    assert "현재 7개" in issue["reason"]
    assert "NHCP DLL" not in issue["reason"]
    assert {"2014yearluck", "lifeluck", "fatewedluck", "loveluck", "todayluck"} <= active.keys()
    value = client.post("/v1/fortunes/yearly", json={
        "birth": BIRTH, "target_date": "2027-01-01", "include_ai": False
    })
    assert value.status_code == 200, value.text
    assert value.json()["analysis"]["ready_for_ai"] is True
    assert value.json()["analysis"]["method"] == "asp-saju-ai-yearly-v1"


def test_core_kind_schema_and_swagger_no_longer_offer_career(api):
    client, schema, _ = api
    assert len(catalog()) == 9
    assert "career" not in {kind.value for kind in FortuneKind}
    assert "career" not in {item["id"] for item in client.get("/v1/fortunes").json()["items"]}
    assert "career_category" not in FortuneRequest.model_fields
    assert "career_category" not in schema["components"]["schemas"]["FortuneRequest"]["properties"]
    assert "career" not in schema["components"]["schemas"]["FortuneKind"]["enum"]
    assert "/v1/fortunes/career" not in schema["paths"]
    original = {item["id"]: item for item in json.loads(RAW_CATALOG.read_text())["items"]}
    for service_id in REMOVED:
        assert f"/v1/un/{service_id}" not in schema["paths"]
        assert original[service_id]["diagnostic_path"] not in schema["paths"]
    assert len(schema["paths"]) == 600
    assert not hasattr(legacy_relationships, "CAREER_TITLES")
    assert not hasattr(legacy_relationships, "career_dispatch")
    assert not hasattr(legacy_relationships, "_career")


@pytest.mark.parametrize("service_id", sorted(REMOVED))
@pytest.mark.parametrize("include_ai", [False, True])
def test_removed_service_ids_cannot_be_run_through_the_hidden_fallback(api, service_id, include_ai):
    client, _, fake = api
    before = client.get("/v1/ai-usage").json()["used"]
    body = {"birth": BIRTH, "target_date": "2027-01-01", "include_ai": include_ai}
    result = client.post(f"/v1/un/{service_id}", json=body)
    assert result.status_code == 404, result.text
    assert result.json()["error"]["code"] == "unknown_service"
    assert client.get("/v1/ai-usage").json()["used"] == before
    fake.interpret.assert_not_called()


def test_career_cannot_reenter_through_the_generic_kind_route(api):
    client, _, fake = api
    before = client.get("/v1/ai-usage").json()["used"]
    body = {"birth": BIRTH, "target_date": "2027-01-01", "include_ai": True}
    result = client.post("/v1/fortunes/career", json=body)
    assert result.status_code in {404, 422}
    assert client.get("/v1/ai-usage").json()["used"] == before
    fake.interpret.assert_not_called()


def test_removed_diagnostic_urls_are_not_available(api):
    client, _, _ = api
    for item in json.loads(RAW_CATALOG.read_text())["items"]:
        if item["id"] in REMOVED:
            assert client.get(item["diagnostic_path"]).status_code == 404
