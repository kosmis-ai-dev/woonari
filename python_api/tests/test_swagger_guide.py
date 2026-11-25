"""CR-002 / T-009: the Korean Swagger guide must be executable, not just labels."""

import re
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app, get_interpreter
from app.models import FortuneRequest, Interpretation

FORTUNES = {
    "daily": "오늘의 un",
    "weekly": "이번주 un",
    "monthly": "이달의 un",
    "yearly": "연간 un",
    "lifetime": "평생un",
    "wealth": "명품 평생재물운",
    "love": "러브 어드바이스",
    "biorhythm": "바이오리듬",
}
DEPENDENT = set()


def korean(value):
    return re.search(r"[가-힣]", value) is not None


@pytest.fixture
def app():
    # All provider calls here are mocked; this does not validate an external AI service.
    fake = SimpleNamespace(
        name="test", model="never-called", interpret=AsyncMock(side_effect=AssertionError),
        close=AsyncMock(),
    )
    application = create_app(
        Settings(_env_file=None, api_key=None, openai_api_key=None, openai_model=""),
        interpreter_factory=lambda _: fake,
    )
    # Calculation examples must never call AI; AI-first examples use an explicit mock.
    application.state.guide_test_interpreter = fake
    application.dependency_overrides[get_interpreter] = lambda: (
        application.state.guide_test_interpreter
    )
    return application


@pytest.fixture
def client(app):
    with TestClient(app) as value:
        yield value


@pytest.fixture
def schema(app):
    return app.openapi()


def operation(schema, kind):
    return schema["paths"][f"/v1/fortunes/{kind}"]["post"]


def examples(schema, kind):
    return operation(schema, kind)["requestBody"]["content"]["application/json"]["examples"]


@pytest.mark.parametrize("kind,name", FORTUNES.items())
def test_each_fortune_has_a_korean_static_test_operation(schema, kind, name):
    endpoint = operation(schema, kind)
    assert name in endpoint["summary"]
    assert korean(endpoint["description"])
    assert endpoint.get("tags")
    assert all(
        p["in"] != "query" and p["name"] != "kind" for p in endpoint.get("parameters", [])
    ), "A fixed fortune endpoint must not accidentally expose its captured kind as input."


@pytest.mark.parametrize("kind", FORTUNES)
def test_first_example_requests_ai_only_for_ready_fortunes(schema, kind):
    samples = examples(schema, kind)
    if kind in DEPENDENT:
        assert list(samples) == ["calculation_only"]
        assert samples["calculation_only"]["value"]["include_ai"] is False
    else:
        assert list(samples) == ["with_ai", "calculation_only"]
        assert samples["with_ai"]["value"]["include_ai"] is True
        assert "content" in samples["with_ai"]["description"]
        assert "ai_not_configured" in samples["with_ai"]["description"]


@pytest.mark.parametrize("kind", FORTUNES)
def test_calculation_swagger_example_is_executable_without_ai(client, app, schema, kind):
    sample = examples(schema, kind)["calculation_only"]
    assert korean(sample["summary"])
    body = sample["value"]
    assert body["include_ai"] is False
    if kind == "yearly":
        assert body["target_date"].startswith("2027-")
    elif kind == "compatibility":
        assert body["partner"]
    response = client.post(f"/v1/fortunes/{kind}", json=body)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["result"]["kind"] == kind
    assert result["result"]["kind"] == kind
    assert result["content"] is None
    assert result["interpretation"] is None
    app.state.guide_test_interpreter.interpret.assert_not_called()


@pytest.mark.parametrize("kind", sorted(set(FORTUNES) - DEPENDENT))
def test_recommended_ai_example_returns_content_from_a_mocked_interpreter(client, app, schema, kind):
    async def interpret(analysis):
        return Interpretation(
            summary="모의 검증용 un 요약입니다.",
            sections=[
                {
                    "target_id": target.id,
                    "topic": target.topic,
                    "text": f"{target.topic}에 대한 모의 검증용 해석입니다.",
                    "evidence_ids": target.evidence_ids,
                }
                for target in analysis.narrative_contract
            ],
            practical_advice=["모의 검증용 실천 조언입니다."],
        )

    fake = app.state.guide_test_interpreter
    fake.interpret.side_effect = interpret
    sample = next(iter(examples(schema, kind).values()))
    response = client.post(f"/v1/fortunes/{kind}", json=sample["value"])
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["result"]["kind"] == kind
    assert result["interpretation"]["summary"] in result["content"]
    assert result["interpretation"]["practical_advice"][0] in result["content"]
    for section in result["interpretation"]["sections"]:
        assert section["topic"] in result["content"]
        assert section["text"] in result["content"]
    fake.interpret.assert_awaited_once()


def test_only_available_fortunes_are_documented(schema):
    ready_tags = {operation(schema, kind)["tags"][0] for kind in FORTUNES}
    assert len(ready_tags) == 1
    assert all(korean(tag) for tag in ready_tags)
    assert "/v1/fortunes/compatibility" not in schema["paths"]


def test_input_limits_are_explained_where_people_test(schema):
    annual = operation(schema, "yearly")["description"]
    assert "2027" in annual and "별점" in annual and "AI" in annual


def test_every_documented_request_example_validates(schema):
    for kind in FORTUNES:
        for sample in examples(schema, kind).values():
            body = FortuneRequest.model_validate(sample["value"])
            assert (body.partner is not None) is (kind == "compatibility")


def test_every_calculation_example_runs_without_ai(client, schema):
    for kind in FORTUNES:
        for sample in examples(schema, kind).values():
            body = sample["value"]
            if not body["include_ai"]:
                response = client.post(f"/v1/fortunes/{kind}", json=body)
                assert response.status_code == 200, (kind, sample["summary"], response.text)


def test_the_existing_generic_endpoint_still_works(client, schema):
    assert "/v1/fortunes/{kind}" in schema["paths"]
    sample = examples(schema, "daily")["calculation_only"]["value"]
    assert client.post("/v1/fortunes/daily", json=sample).status_code == 200
    assert client.post("/v1/fortunes/not-a-fortune", json=sample).status_code == 422


def test_schema_contains_korean_input_field_help(schema):
    model_fields = {
        "Birth": ("year", "month", "day", "hour", "minute", "calendar", "gender", "leap_month"),
        "FortuneRequest": ("birth", "target_date", "include_ai", "partner"),
        "SajuRequest": ("birth", "calculation_profile"),
    }
    for model, fields in model_fields.items():
        for field in fields:
            prop = schema["components"]["schemas"][model]["properties"][field]
            assert korean(prop.get("description", "")), (model, field)


def test_the_guide_explains_clicks_and_response_fields(schema):
    guide = schema["info"]["description"]
    assert "Try it out" in guide and "Execute" in guide
    assert "include_ai" in guide
    assert "result" in guide and "interpretation" in guide
    assert "ready_for_ai" not in guide
    assert "content" in guide
    assert "ai_not_configured" in guide
    assert "AI" in guide


def test_saju_example_can_be_executed_directly(client, schema):
    endpoint = schema["paths"]["/v1/saju"]["post"]
    assert korean(endpoint["summary"])
    sample = next(iter(endpoint["requestBody"]["content"]["application/json"]["examples"].values()))
    response = client.post("/v1/saju", json=sample["value"])
    assert response.status_code == 200
    assert len(response.json()["pillars"]) == 4


def test_corrected_lunar_example_returns_the_distinct_leap_date(client, schema):
    endpoint = schema["paths"]["/v1/saju"]["post"]
    samples = endpoint["requestBody"]["content"]["application/json"]["examples"]
    body = samples["corrected_lunar_leap"]["value"]
    result = client.post("/v1/saju", json=body)
    assert result.status_code == 200
    assert result.json()["solar_birth"].startswith("2023-04-19T")
    assert result.json()["lunar_birth"]["leap_month"] is True
    assert "policy" not in result.json()
    body["birth"]["leap_month"] = False
    regular = client.post("/v1/saju", json=body)
    assert regular.status_code == 200
    assert regular.json()["solar_birth"].startswith("2023-03-20T")


def test_guide_explains_lunar_input_without_internal_correction_metadata(schema):
    guide = schema["info"]["description"]
    assert "음력" in guide and "윤달" in guide
    assert "lunar-leap-flags-v1" not in guide
    assert "ASP" not in guide


def test_operations_have_distinct_ids(schema):
    ids = [
        operation["operationId"]
        for path in schema["paths"].values()
        for method, operation in path.items()
        if method in {"get", "post", "put", "patch", "delete", "head", "options"}
    ]
    assert len(ids) == len(set(ids))
