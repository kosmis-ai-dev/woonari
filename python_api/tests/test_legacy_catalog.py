"""CR-004: full source coverage and honest Swagger diagnostics, without ASP execution."""

import json
from collections import Counter
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.legacy_catalog import full_catalog, services
from app.main import create_app
from app.service_engine import handlers
from tools.source_inventory import load_snapshot

ROOT = Path(__file__).resolve().parents[2]


def test_all_original_directories_and_nested_results_are_accounted_for():
    inventory = load_snapshot()
    # T-025 exports contain Python, not ASP. Pin the complete audited source tree
    # so deleting rows from a fixture cannot silently weaken coverage checks.
    assert inventory["source_tree_sha256"] == "e2902d0cfd9ad7e7081a5d4e3c8f307997744ed7596764f9b1ce3b440a28bb33"
    asp_paths = {path for path in inventory["files"] if path.lower().endswith(".asp")}
    assert len(asp_paths) == 1445
    assert sum(inventory["files"][path]["lines"] for path in asp_paths) == 499008
    items = json.loads((ROOT / "python_api/app/data/legacy_services.json").read_text())["items"]
    directories = {item["directory"] for item in items}
    expected = set(inventory["unse_directories"])
    assert expected <= directories
    covered = {path for item in items for path in item["entrypoints"]}
    results = {path for path in asp_paths if path.startswith("old/unse/interlife/UNSE_DATA/unse/")}
    assert results and results <= covered
    adult_results = {path for path in asp_paths
                     if path.startswith("old/unse/adultluck/") and path.endswith("/main_end.asp")
                     and path.count("/") == 4}
    assert adult_results and adult_results <= covered


def test_service_names_evidence_and_dependency_remedies_are_concrete():
    source_files = load_snapshot()["files"]
    items = services()
    ids = {item["id"] for item in items}
    assert len(items) == len(ids)
    for item in items:
        assert any("가" <= char <= "힣" for char in item["original_name"]), item["id"]
        assert item["sources"], item["id"]
        assert set(item["children"]) <= ids
        if item["parent_id"]:
            parent = next(parent for parent in items if parent["id"] == item["parent_id"])
            assert item["id"] in parent["children"]
        for source in item["sources"] + [ref for issue in item["issues"] for ref in issue["sources"]]:
            assert source["path"] in source_files, source
            assert 1 <= source["line"] <= source_files[source["path"]]["lines"], source
        if item["status"] in {"not_ported", "source_required", "archived"}:
            assert item["issues"], item["id"]
        for issue in item["issues"]:
            assert issue["reason"] and issue["effect"] and issue["resolution"], item["id"]


def test_all_original_xml_menu_declarations_have_a_traced_target():
    inventory = load_snapshot()
    assert inventory["xml_menu"]["source"] in inventory["files"]
    declared = {node["content_code"]: node["original_name"] for node in inventory["xml_menu"]["declarations"]}
    assert len(declared) == len(inventory["xml_menu"]["declarations"])
    app = create_app(Settings(_env_file=None, api_key=None))
    with TestClient(app) as client:
        data = client.get("/v1/asp-services").json()
    actual = {entry["content_code"]: entry["original_name"] for entry in data["menu_map"]}
    retired_menus = {"IM9", "IM14", "IM34", "IM62", "IM70", "IM71"}
    assert actual == {key: name for key, name in declared.items() if key not in retired_menus}
    frozen = json.loads((ROOT / "python_api/app/data/legacy_services.json").read_text())
    assert {entry["content_code"]: entry["original_name"] for entry in frozen["menu_map"]} == declared
    by_id = {item["id"]: item for item in data["items"]}
    for entry in data["menu_map"]:
        assert entry["content_code"] in by_id[entry["catalog_id"]]["menu_codes"]


def test_audited_source_files_still_match_the_catalog_snapshot():
    # Keep both original manifests byte-for-byte. Frozen inventory hashes verify
    # their provenance without pretending absent ASP files were re-read.
    source_files = load_snapshot()["files"]
    for name in ("catalog_source_manifest.json", "source_manifest.json"):
        manifest = json.loads((ROOT / "python_api/docs" / name).read_text())
        assert manifest["sources"]
        for entry in manifest["sources"]:
            assert source_files[entry["path"]]["sha256"] == entry["sha256"], entry["path"]


def test_every_catalog_entry_is_visible_and_executable_as_a_diagnostic():
    app = create_app(Settings(_env_file=None, api_key=None, openai_api_key=None, openai_model=""))
    schema = app.openapi()
    with TestClient(app) as client:
        response = client.get("/v1/asp-services")
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["records"] == len(data["items"])
        assert data["ai_configuration"]["key_configured"] is False
        assert data["ai_configuration"]["provider"] == "openai"
        assert data["ai_configuration"]["authentication"] == "api_key"
        assert data["ai_configuration"]["key_required"] is True
        assert data["ai_configuration"]["configuration_complete"] is False
        assert data["ai_configuration"]["generation_check"] == "not_run"
        for item in data["items"]:
            operation = schema["paths"][item["diagnostic_path"]]["get"]
            assert item["name"] in operation["summary"]
            assert "원인" in operation["description"] or not item["issues"]
            assert "Try it out" in operation["description"]
            # Capturing a row in a handler must not create a query/body parameter.
            assert not operation.get("requestBody")
            assert all(p["in"] == "header" for p in operation.get("parameters", []))
            result = client.get(item["diagnostic_path"])
            assert result.status_code == 200, result.text
            assert result.json() == item, item["id"]


def test_catalog_reports_current_ports_without_claiming_every_entry_can_calculate():
    items = services()
    registered = handlers()
    assert len(registered) == 166
    assert Counter(item["status"] for item in items) == {
        "ready": 63, "calculation_only": 2, "source_required": 201,
        "reference": 17, "archived": 8
    }
    existing = {item["api_kind"]: item["test_path"] for item in items if item["api_kind"]}
    kinds = {
        "daily", "weekly", "monthly", "yearly", "lifetime", "wealth", "love",
        "compatibility", "biorhythm"
    }
    assert existing == {kind: f"/v1/fortunes/{kind}" for kind in kinds}
    for item in items:
        if item["id"] in registered:
            metadata = registered[item["id"]][1]
            expected = "source_required" if not metadata.get("ready", True) else (
                "calculation_only" if metadata.get("calculation_only") else "ready"
            )
            assert item["status"] == expected, item["id"]
            assert item["test_path"] == f"/v1/un/{item['id']}", item["id"]
            assert bool(item["issues"]) is (expected == "source_required"), item["id"]
            assert any(dependency.get("kind") == "python_port" for dependency in item["dependencies"])
        elif not item["api_kind"]:
            assert item["test_path"] is None
        assert item["status"] != "not_ported"
        assert not any(issue["code"] == "python_not_ported" for issue in item["issues"])


def test_catalog_preserves_distinct_missing_source_and_external_dependencies():
    items = {item["id"]: item for item in services()}
    for service_id, expected in {
        "interlife-free-9": "result_source_missing",
        "loveunse-love-today": "result_branch_missing",
        "external-video-a": "external_implementation_missing",
        "interlife-yukim-1": "interlife_woljang_classification_unverified",
        "interlife-jum-2": "interlife_indirect_numeric_score_missing"
    }.items():
        assert items[service_id]["status"] == "source_required"
        assert expected in {issue["code"] for issue in items[service_id]["issues"]}
        assert items[service_id]["test_path"] == (
            f"/v1/un/{service_id}" if service_id in handlers() else None
        )
    external = [item for item in items.values() if item["id"].startswith("external-video-")]
    assert len(external) == 6
    assert all(item["status"] == "source_required" for item in external)


def test_catalog_counts_are_contract_readiness_and_keep_external_ai_gate_separate():
    data = full_catalog(
        ai_provider="bedrock", ai_key_configured=None,
        ai_model_configured=True, ai_region_configured=True
    )
    assert data["summary"]["python_execution"]["additional_registered"] == 166
    assert data["summary"]["python_execution"]["implemented_records_including_existing"] == 175
    assert data["summary"]["python_execution"]["source_required_without_handler"] == 91
    assert data["summary"]["python_execution"]["ready_does_not_verify_external_ai_generation"] is True
    assert data["ai_configuration"]["generation_check"] == "not_run"
    assert any("FTU" in note and "실제 AI 생성 성공을 보장하지 않습니다" in note for note in data["common_notes"])


def test_new_catalog_routes_keep_api_key_protection_and_never_return_secret_values():
    key = "test-secret-value-never-expose"
    app = create_app(Settings(_env_file=None, api_key=key, openai_api_key=key, openai_model="test"))
    with TestClient(app) as client:
        assert client.get("/v1/asp-services").status_code == 401
        first = services()[0]["diagnostic_path"]
        assert client.get(first).status_code == 401
        response = client.get("/v1/asp-services", headers={"X-API-Key": key})
        assert response.status_code == 200
        assert response.json()["ai_configuration"]["key_configured"] is True
        assert key not in response.text
    # Source paths and facts are public documentation; legacy connection strings aren't.
    assert key not in json.dumps(app.openapi())


@pytest.mark.parametrize("model,region,complete", [
    (False, False, False), (True, False, False), (False, True, False), (True, True, True),
])
def test_bedrock_catalog_uses_iam_and_reports_only_static_configuration(model, region, complete):
    configuration = full_catalog(
        ai_provider="bedrock", ai_key_configured=None,
        ai_model_configured=model, ai_region_configured=region,
    )["ai_configuration"]
    assert configuration["provider"] == "bedrock"
    assert configuration["authentication"] == "aws_iam"
    assert configuration["key_required"] is False
    assert configuration["key_configured"] is None
    assert configuration["region_configured"] is region
    assert configuration["model_configured"] is model
    assert configuration["configuration_complete"] is complete
    assert configuration["generation_check"] == "not_run"


def test_bedrock_catalog_get_does_not_request_an_openai_key_or_expose_model_names():
    application = create_app(Settings(
        _env_file=None, ai_provider="bedrock", bedrock_model_id="fixture-private-model-id",
        bedrock_region="ap-southeast-2", openai_api_key=None, openai_model="",
    ))
    with TestClient(application) as client:
        response = client.get("/v1/asp-services")
    assert response.status_code == 200
    assert response.json()["ai_configuration"]["key_configured"] is None
    assert response.json()["ai_configuration"]["configuration_complete"] is True
    assert response.json()["ai_configuration"]["generation_check"] == "not_run"
    assert "fixture-private-model-id" not in response.text
