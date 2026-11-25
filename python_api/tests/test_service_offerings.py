"""CR-020 / T-040: the service group contains only the curated canonical APIs.

Model calls and restored SQL rows are synthetic. These tests validate the public
selection, input examples, response contracts and no-call calculation mode; they
do not certify real model prose or the production database.
"""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from test_source_archive import Connection, spec

import app.source_archive as archive
from app.ai_quota import DailyAIQuota
from app.config import Settings
from app.main import create_app
from app.models import Interpretation
from app.service_offerings import SERVICE_TAG

CORE_PATHS = {
    f"/v1/fortunes/{kind}" for kind in
    ("daily", "weekly", "monthly", "yearly", "lifetime", "wealth", "love", "biorhythm")
}
EXTRA_PATHS = {
    f"/v1/un/{identifier}" for identifier in (
        "sweetluck", "studentluck", "humanorganizationmanagement", "meetluck", "ddiluck",
        "ourgrowthluck", "flowerluck", "jewelryluck", "preluck"
    )
}
FLOWER_STONE_PATHS = {"/v1/un/flowerluck", "/v1/un/jewelryluck"}
EXPECTED_PATHS = CORE_PATHS | EXTRA_PATHS


def offered(schema):
    return {
        path: operations["post"] for path, operations in schema["paths"].items()
        if "post" in operations and SERVICE_TAG in operations["post"].get("tags", [])
    }


def samples(operation):
    return operation["requestBody"]["content"]["application/json"]["examples"]


def mock_interpretation(analysis):
    return Interpretation(
        summary="검증용 근거에 따른 해석입니다.",
        sections=[{
            "target_id": target.id, "topic": target.topic,
            "text": "제공된 사주와 항목 근거를 살펴 생활 계획을 정리해 보세요.",
            "evidence_ids": target.evidence_ids
        } for target in analysis.narrative_contract],
        practical_advice=["생활의 우선순위를 정해 보세요."]
    )


def synthetic_sources(monkeypatch):
    """Exercise actual flower/stone provenance checks with bounded fake rows.

    Other consumers keep their no-archive fixture decisions. Their production
    archive integrations are covered in test_source_archive, not faked as valid
    rows by this Swagger selection test.
    """
    registry = {"format": archive.FORMAT, "tables": []}
    connection = Connection(registry)
    flower = spec("TB_FlowerLuck", "woonari_source_tb_flowerluck", [
        "fw_no", "month", "day", "name_h", "name_e", "fw_word", "fw_column", "origin",
        "story", "unse"
    ])
    stone = spec("TB_birthStoneLuck", "woonari_source_tb_birthstoneluck", [
        "idx", "birthMon_ref", "stoneName_kor", "stoneName_en", "stoneLang", "contents"
    ])
    flower["row_count"] = stone["row_count"] = 2
    registry["tables"] = [flower, stone]
    connection.records[flower["target_table"]] = [{
        "fw_no": ordinal, "month": month, "day": day,
        "name_h": "예시꽃", "name_e": "Example flower", "fw_word": "관심",
        "fw_column": "예시 분류", "origin": "예시 원산지",
        "story": "작은 관심의 전통 이야기", "unse": "꾸준한 관찰을 권합니다."
    } for ordinal, (month, day) in enumerate(((3, 2), (5, 17)), 1)]
    connection.records[stone["target_table"]] = [{
        "idx": ordinal, "birthMon_ref": month, "stoneName_kor": "예시보석",
        "stoneName_en": "Example stone", "stoneLang": "관심", "contents": "차분한 관찰을 권합니다."
    } for ordinal, month in enumerate((3, 5), 1)]
    connection.freeze()
    monkeypatch.setattr(archive, "_registry", lambda: (deepcopy(registry), "c" * 64))
    store = archive.MySQLSourceArchiveStore(lambda: connection)
    selective = SimpleNamespace(resolve=lambda service, decision: (
        store.resolve(service, decision)
        if service in {"flowerluck", "jewelryluck"} else deepcopy(decision)
    ))
    monkeypatch.setattr(archive, "_factory", lambda: selective)


def build_api(private):
    fake = SimpleNamespace(
        name="offering-test", model="no-network-model",
        interpret=AsyncMock(side_effect=mock_interpretation), close=AsyncMock()
    )
    app = create_app(
        Settings(_env_file=None, api_key=None, openai_api_key=None, openai_model=""),
        interpreter_factory=lambda _: fake,
        ai_quota=DailyAIQuota(private / "ai/usage.sqlite3", private_root=private, limit=100)
    )
    return app, fake


@pytest.fixture(scope="module")
def api_with_sources(tmp_path_factory):
    with pytest.MonkeyPatch.context() as monkeypatch:
        synthetic_sources(monkeypatch)
        app, fake = build_api(tmp_path_factory.mktemp("service-offering-api"))
        with TestClient(app) as client:
            yield client, app.openapi(), fake


@pytest.fixture(scope="module")
def offline_schema(tmp_path_factory):
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(archive, "_factory", None)
        app, _ = build_api(tmp_path_factory.mktemp("service-offering-offline"))
        schema = app.openapi()
    return schema


def test_service_group_is_first_and_contains_exactly_17_canonical_apis(api_with_sources):
    _, schema, _ = api_with_sources
    assert schema["tags"][0]["name"] == SERVICE_TAG
    assert len({item["name"] for item in schema["tags"]}) == len(schema["tags"])
    assert set(offered(schema)) == EXPECTED_PATHS
    assert len(offered(schema)) == 17
    assert len(schema["paths"]) == 600
    ids = [op["operationId"] for ops in schema["paths"].values() for method, op in ops.items()
           if method in {"get", "post", "put", "patch", "delete", "options", "head"}]
    assert len(ids) == len(set(ids))


def test_missing_source_connection_does_not_promote_flower_or_stone(offline_schema):
    assert set(offered(offline_schema)) == EXPECTED_PATHS - FLOWER_STONE_PATHS
    for path in FLOWER_STONE_PATHS:
        operation = offline_schema["paths"][path]["post"]
        assert SERVICE_TAG not in operation["tags"]
        assert next(iter(samples(operation).values()))["value"]["include_ai"] is False


def test_aliases_diagnostics_and_general_advice_are_not_in_the_service_group(api_with_sources):
    _, schema, _ = api_with_sources
    excluded = {
        "/v1/fortunes/compatibility", "/v1/fortunes/{kind}",
        "/v1/un/todayluck", "/v1/un/2014yearluck", "/v1/un/lifeluck",
        "/v1/un/perluck", "/v1/un/analysisluck", "/v1/un/carluck", "/v1/un/lottoluck",
        "/v1/un/interlife-free-12", "/v1/un/interlife-manse-2"
    }
    assert not excluded & set(offered(schema))
    for path, ops in schema["paths"].items():
        if "get" in ops:
            assert SERVICE_TAG not in ops["get"].get("tags", [])
        if path in offered(schema):
            assert "본문" in ops["post"]["summary"]
    assert schema["paths"]["/v1/un/analysisluck"]["post"]["tags"] == ["기타 콘텐츠 · AI 해석"]
    assert schema["paths"]["/v1/un/interlife-free-12"]["post"]["tags"] == ["계산 도구 · 본문 없음"]
    assert "/v1/un/animalluck" not in schema["paths"]


@pytest.mark.parametrize("path", sorted(EXPECTED_PATHS))
def test_offered_examples_generate_contract_bound_mock_prose_and_calculation_is_free(api_with_sources, path):
    client, schema, fake = api_with_sources
    operation = offered(schema)[path]
    examples = samples(operation)
    body = next(iter(examples.values()))["value"]
    assert body["include_ai"] is True
    assert any(example["value"]["include_ai"] is False for example in examples.values())
    fake.interpret.reset_mock()
    used = client.get("/v1/ai-usage").json()["used"]
    baseline = client.post(path, json={**body, "include_ai": False})
    assert baseline.status_code == 200, (path, baseline.text)
    value = baseline.json()
    assert value["content"] is None and value["interpretation"] is None
    assert value["analysis"]["ready_for_ai"] is True
    assert value["analysis"]["narrative_contract"]
    fake.interpret.assert_not_called()
    assert client.get("/v1/ai-usage").json()["used"] == used
    generated = client.post(path, json=body)
    assert generated.status_code == 200, (path, generated.text)
    result = generated.json()
    assert result["analysis"] == value["analysis"]
    assert result["content"]
    targets = {target["id"] for target in value["analysis"]["narrative_contract"]}
    assert {section["target_id"] for section in result["interpretation"]["sections"]} == targets
    fake.interpret.assert_awaited_once()


def test_service_input_conditions_are_visible_in_the_operations(api_with_sources):
    _, schema, _ = api_with_sources
    operations = offered(schema)
    growth = operations["/v1/un/ourgrowthluck"]
    assert "상대" in growth["description"]
    assert next(iter(samples(growth).values()))["value"]["partner"]
    assert "양력" in operations["/v1/un/jewelryluck"]["description"]
    assert "12띠" in operations["/v1/un/ddiluck"]["description"]
    assert "상징" in operations["/v1/un/preluck"]["description"]
    assert "주기" in operations["/v1/fortunes/biorhythm"]["description"]
    annual = operations["/v1/fortunes/yearly"]
    assert next(iter(samples(annual).values()))["value"]["target_date"].startswith("2027-")
