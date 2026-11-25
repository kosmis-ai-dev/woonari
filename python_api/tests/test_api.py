from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.fortunes import analyze
from app.main import create_app, get_interpreter
from app.models import FortuneKind, FortuneRequest, Interpretation


@pytest.fixture
def app():
    return create_app(Settings(_env_file=None, openai_api_key=None, openai_model="", api_key=None))


@pytest.fixture
def client(app):
    with TestClient(app) as value:
        yield value


@pytest.fixture
def payload():
    return {
        "birth": {"year": 1990, "month": 5, "day": 17, "hour": 14, "minute": 30, "gender": "male"},
        "target_date": "2026-11-02",
        "include_ai": False,
    }


def test_health_catalog_and_openapi(client):
    health = client.get("/health").json()
    assert health["status"] == "ok"
    assert health["ai_provider"] == "openai"
    assert health["ai_configured"] is False
    assert health["ai_missing_settings"] == ["OPENAI_API_KEY", "OPENAI_MODEL"]
    assert len(client.get("/v1/fortunes").json()["items"]) == 8
    assert "/v1/saju" in client.get("/openapi.json").json()["paths"]
    assert client.get("/docs").status_code == 200


def test_saju_and_calculation_only(client, payload):
    result = client.post("/v1/saju", json={"birth": payload["birth"]})
    assert result.status_code == 200
    assert len(result.json()["pillars"]) == 4
    fortune = client.post("/v1/fortunes/daily", json=payload)
    assert fortune.status_code == 200
    assert next(iter(fortune.json())) == "content"
    assert fortune.json()["content"] is None
    assert fortune.json()["interpretation"] is None
    assert len(fortune.json()["result"]["scores"]) == 8


@pytest.mark.parametrize(
    "kind",
    [
        "daily",
        "weekly",
        "monthly",
        "yearly",
        "lifetime",
        "wealth",
        "love",
        "biorhythm",
        "compatibility",
    ],
)
def test_all_routes(client, payload, kind):
    if kind == "compatibility":
        payload["partner"] = payload["birth"] | {"year": 1992, "gender": "female"}
    if kind == "yearly":
        payload["target_date"] = "2014-11-02"
    assert client.post(f"/v1/fortunes/{kind}", json=payload).status_code == (503 if kind == "compatibility" else 200)


def test_ai_misconfiguration_is_explicit(client, payload):
    payload["include_ai"] = True
    result = client.post("/v1/fortunes/daily", json=payload)
    assert result.status_code == 503
    assert result.json()["error"]["code"] == "ai_not_configured"
    assert "content" not in result.json()


def test_successful_ai_result_preserves_analysis(app, client, payload):
    baseline = client.post("/v1/fortunes/daily", json=payload).json()["result"]
    contract = analyze(FortuneKind.daily, FortuneRequest(**payload)).model_dump(mode="json")
    interpretation = Interpretation(
        summary="오늘의 해석",
        sections=[
            {
                "target_id": t["id"],
                "topic": t["topic"],
                "text": f"{t['topic']}에 관한 계산에 따른 제안",
                "evidence_ids": t["evidence_ids"],
            }
            for t in contract["narrative_contract"]
        ],
        practical_advice=["순서를 정하세요.", "일정에 여유를 두세요."],
    )
    fake = SimpleNamespace(
        name="test", model="fixture-model", interpret=AsyncMock(return_value=interpretation)
    )
    app.dependency_overrides[get_interpreter] = lambda: fake
    payload["include_ai"] = True
    result = client.post("/v1/fortunes/daily", json=payload)
    assert result.status_code == 200
    assert result.json()["result"] == baseline
    assert "ai_model" not in result.json()
    assert result.json()["interpretation"]["summary"] == "오늘의 해석"
    assert next(iter(result.json())) == "content"
    assert result.json()["content"] == (
        "오늘의 해석\n\n"
        "어제의 운세\n어제의 운세에 관한 계산에 따른 제안\n\n"
        "오늘의 운세\n오늘의 운세에 관한 계산에 따른 제안\n\n"
        "내일의 운세\n내일의 운세에 관한 계산에 따른 제안\n\n"
        "실천 조언\n- 순서를 정하세요.\n- 일정에 여유를 두세요."
    )


@pytest.mark.parametrize(
    "key,model,missing",
    [
        (None, "", ["OPENAI_API_KEY", "OPENAI_MODEL"]),
        ("fixture-key-private", "", ["OPENAI_MODEL"]),
        (None, "fixture-model-private", ["OPENAI_API_KEY"]),
        ("fixture-key-private", "fixture-model-private", []),
    ],
)
def test_health_only_reports_ai_setting_presence_without_exposing_values(key, model, missing):
    application = create_app(Settings(
        _env_file=None, openai_api_key=key, openai_model=model, api_key="fixture-api-private",
    ))
    with TestClient(application) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ai_configured"] is (not missing)
    assert response.json()["ai_missing_settings"] == missing
    assert "fixture-key-private" not in response.text
    assert "fixture-model-private" not in response.text
    assert "fixture-api-private" not in response.text


@pytest.mark.parametrize(
    "model,region,missing",
    [
        ("", "", ["BEDROCK_MODEL_ID", "BEDROCK_REGION"]),
        ("fixture-bedrock-model", "", ["BEDROCK_REGION"]),
        ("", "ap-southeast-2", ["BEDROCK_MODEL_ID"]),
        ("fixture-bedrock-model", "ap-southeast-2", []),
    ],
)
def test_bedrock_health_checks_selected_provider_settings_and_never_uses_openai(
    monkeypatch, model, region, missing,
):
    openai = Mock(side_effect=AssertionError("Bedrock selection must not create OpenAI."))
    monkeypatch.setattr("app.main.OpenAIInterpreter", openai)
    application = create_app(Settings(
        _env_file=None, ai_provider="bedrock", bedrock_model_id=model, bedrock_region=region,
        openai_api_key=None, openai_model="",
    ))
    with TestClient(application) as client:
        response = client.get("/health")
        assert application.state.interpreter.name == "bedrock"
    assert response.status_code == 200
    assert response.json()["ai_provider"] == "bedrock"
    assert response.json()["ai_configured"] is (not missing)
    assert response.json()["ai_missing_settings"] == missing
    assert "fixture-bedrock-model" not in response.text
    openai.assert_not_called()


def test_custom_bedrock_interpreter_factory_generates_content_and_closes(client, payload):
    baseline = client.post("/v1/fortunes/daily", json=payload).json()["result"]
    contract = analyze(FortuneKind.daily, FortuneRequest(**payload)).model_dump(mode="json")
    interpretation = Interpretation(
        summary="Bedrock가 작성한 해석",
        sections=[
            {"target_id": item["id"], "topic": item["topic"], "text": "근거에 따른 제안",
             "evidence_ids": item["evidence_ids"]}
            for item in contract["narrative_contract"]
        ],
        practical_advice=["계획을 확인하세요."],
    )
    configured = Settings(
        _env_file=None, ai_provider="bedrock", bedrock_model_id="fixture-bedrock-model",
        bedrock_region="ap-southeast-2", openai_api_key=None, openai_model="",
    )
    interpreter = SimpleNamespace(
        name="bedrock", model="fixture-bedrock-model",
        interpret=AsyncMock(return_value=interpretation), close=AsyncMock(),
    )
    factory = Mock(return_value=interpreter)
    application = create_app(configured, interpreter_factory=factory)
    with TestClient(application) as injected:
        assert injected.get("/health").json()["ai_configured"] is True
        assert injected.post("/v1/fortunes/daily", json=payload).json()["content"] is None
        interpreter.interpret.assert_not_called()
        result = injected.post("/v1/fortunes/daily", json=payload | {"include_ai": True})
    assert result.status_code == 200
    assert result.json()["content"].startswith("Bedrock가 작성한 해석\n\n")
    assert "계획을 확인하세요." in result.json()["content"]
    assert result.json()["result"] == baseline
    assert "ai_provider" not in result.json()
    assert "ai_model" not in result.json()
    factory.assert_called_once_with(configured)
    interpreter.interpret.assert_awaited_once()
    interpreter.close.assert_awaited_once_with()


def test_bedrock_without_project_invoker_never_falls_back_to_openai(payload):
    application = create_app(Settings(
        _env_file=None, ai_provider="bedrock", bedrock_model_id="fixture-bedrock-model",
        bedrock_region="ap-southeast-2", openai_api_key=None, openai_model="",
    ))
    with TestClient(application) as client:
        response = client.post("/v1/fortunes/daily", json=payload | {"include_ai": True})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "bedrock_not_configured"
    assert "content" not in response.json()


@pytest.mark.parametrize(
    "changes",
    [
        {"year": "1990"},
        {"year": True},
        {"month": 2, "day": 30},
        {"hour": 24},
        {"calendar": "solar", "leap_month": True},
        {"year": 2051},
        {"extra": "unexpected"},
    ],
)
def test_invalid_birth_inputs_are_422(client, payload, changes):
    payload["birth"].update(changes)
    result = client.post("/v1/fortunes/daily", json=payload)
    assert result.status_code == 422
    assert "input" not in result.json()["error"]


def test_invalid_lunar_and_missing_partner_are_422(client, payload):
    payload["birth"].update(year=2024, month=2, day=1, calendar="lunar", leap_month=True)
    assert client.post("/v1/saju", json={"birth": payload["birth"]}).status_code == 422
    assert client.post("/v1/fortunes/compatibility", json=payload).status_code == 422
    assert client.post("/v1/fortunes/unknown", json=payload).status_code == 422


def test_api_key_is_enforced_without_affecting_health(payload):
    secured = create_app(Settings(_env_file=None, api_key="test-secret", openai_api_key=None))
    with TestClient(secured) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/v1/fortunes").status_code == 401
        assert client.post("/v1/fortunes/daily", json=payload).status_code == 401
        assert client.get("/v1/fortunes", headers={"X-API-Key": "wrong"}).status_code == 401
        assert client.get("/v1/fortunes", headers={"X-API-Key": "test-secret"}).status_code == 200


def test_unresolved_source_dependency_never_calls_ai(app, client, payload):
    fake = SimpleNamespace(name="test", model="fixture", interpret=AsyncMock())
    app.dependency_overrides[get_interpreter] = lambda: fake
    payload.update(partner=payload["birth"] | {"year": 1992, "gender": "female"}, include_ai=True)
    result = client.post("/v1/fortunes/compatibility", json=payload)
    assert result.status_code == 503
    assert result.json()["error"]["code"] == "result_unavailable"
    fake.interpret.assert_not_called()
    payload["include_ai"] = False
    unavailable = client.post("/v1/fortunes/compatibility", json=payload)
    assert unavailable.status_code == 503
    assert unavailable.json()["error"]["code"] == "result_unavailable"
    fake.interpret.assert_not_called()
