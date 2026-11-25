"""CR-021 / T-041: responses contain public results, not implementation records."""

import json
import re
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.errors import DomainError
from app.fortunes import analyze
from app.main import create_app
from app.models import Evidence, FortuneKind, FortuneRequest, Interpretation
from app.public_results import clean_result_values, fortune_response, saju_result, service_response
from app.service_engine import analyze_service
from app.service_models import ServiceRequest

BIRTH = {"year": 1974, "month": 3, "day": 2, "hour": 8, "minute": 30, "gender": "male"}
FORBIDDEN_KEYS = {
    "analysis", "source", "source_file", "source_archive", "provenance", "method", "notes",
    "policy", "legacy_memno", "selectors", "narrative_contract", "evidence_ids", "target_id",
    "ready_for_ai", "unresolved_dependencies", "ai_provider", "ai_model", "python_module",
    "major_luck", "calendar_action"
}
INTERNAL_TEXT = re.compile(r"\bASP\b|\.asp\b|\blegacy[_ -]|\bsource_file\b|원본 순서|원본 번호 선택|선택키", re.IGNORECASE)


def assert_public_payload(value):
    """Assert the whole tree, including nested calculation values, is public."""
    if isinstance(value, dict):
        assert not FORBIDDEN_KEYS & value.keys()
        for key, child in value.items():
            assert not INTERNAL_TEXT.search(key), key
            assert_public_payload(child)
    elif isinstance(value, list):
        for child in value:
            assert_public_payload(child)
    elif isinstance(value, str):
        assert not INTERNAL_TEXT.search(value), value


def analysis():
    return analyze(FortuneKind.yearly, FortuneRequest(
        birth=BIRTH, target_date="2027-01-01", include_ai=False
    ))


def test_projection_keeps_values_and_never_changes_the_internal_calculation():
    internal = analysis()
    internal.evidence.append(Evidence(
        id="projection-fixture", topic="검증 계산", source="private/example.asp:1",
        facts={
            "zero": 0, "false": False, "empty": None, "scores": [0, False, None],
            "nested": {"value": 7, "source_file": "private/example.asp", "method": "ASP"},
            "original_source": "private/example.asp", "source_anchors": {"text": "internal"},
            "verified_source_facts": {"values": {"name": "예시꽃", "symbol": "관심"}},
            "legacy_age": 54, "implementation_note": "ASP 이식 기록"
        }
    ))
    before = deepcopy(internal.model_dump(mode="json"))
    result = fortune_response(internal).model_dump(mode="json")
    assert_public_payload(result)
    assert result["content"] is None and result["interpretation"] is None
    assert set(result) == {"content", "interpretation", "result"}
    calculation = result["result"]["calculations"][-1]["values"]
    assert calculation == {
        "zero": 0, "false": False, "empty": None, "scores": [0, False, None],
        "nested": {"value": 7}, "classification": {"name": "예시꽃", "symbol": "관심"},
        "age": 54
    }
    assert result["result"]["scores"] == before["scores"]
    assert result["result"]["saju"]["pillars"] == before["saju"]["pillars"]
    assert internal.model_dump(mode="json") == before


def test_source_metadata_is_filtered_at_any_depth_but_zero_values_survive():
    original = {
        "rows": [{"amount": 0, "active": False, "source": "private/file.asp", "unused": None}],
        "profile": {"source": "private/file.asp", "result": "좋음"},
        "source_table": "internal_table", "notes": ["internal"], "path": "old/unse/demo.asp"
    }
    before = deepcopy(original)
    assert clean_result_values(original) == {
        "rows": [{"amount": 0, "active": False, "unused": None}],
        "profile": {"result": "좋음"}
    }
    assert original == before


def test_interpretation_exposes_only_readable_sections_and_preserves_validated_text():
    internal = analysis()
    interpretation = Interpretation(
        summary="계획을 차분하게 정리해 보세요.",
        sections=[{
            "target_id": target.id, "topic": target.topic, "text": "생활의 우선순위를 살펴보세요.",
            "evidence_ids": target.evidence_ids
        } for target in internal.narrative_contract],
        practical_advice=["작은 계획부터 기록해 보세요."]
    )
    before = interpretation.model_dump(mode="json")
    response = fortune_response(internal, interpretation).model_dump(mode="json")
    assert response["content"] == interpretation.render_text()
    assert response["interpretation"]["summary"] == interpretation.summary
    assert all(set(section) == {"topic", "text"} for section in response["interpretation"]["sections"])
    assert_public_payload(response)
    assert interpretation.model_dump(mode="json") == before
    interpretation.summary = "ASP 원본 파일을 확인했습니다."
    with pytest.raises(DomainError) as error:
        fortune_response(internal, interpretation)
    assert error.value.status == 502


def test_public_saju_contains_only_birth_and_calculation_data():
    internal = analysis().saju
    result = saju_result(internal).model_dump(mode="json")
    assert set(result) == {
        "solar_birth", "lunar_birth", "pillars", "day_master", "elements", "solar_term_window"
    }
    assert result["pillars"] == internal.model_dump(mode="json")["pillars"]
    assert_public_payload(result)


def test_openapi_has_no_implementation_text_or_response_components():
    app = create_app(Settings(_env_file=None, api_key=None, openai_api_key=None, openai_model=""))
    schema = app.openapi()
    encoded = json.dumps(schema, ensure_ascii=False)
    assert not INTERNAL_TEXT.search(encoded)
    assert "원본" not in encoded and "이식" not in encoded
    assert not any(path in schema["paths"] for path in (
        "/v1/asp-services", "/v1/source-data", "/v1/restored-data", "/v1/fortunes/compatibility"
    ))
    assert "Analysis" not in schema["components"]["schemas"]
    assert "ServiceAnalysis" not in schema["components"]["schemas"]
    assert "CalendarPolicy" not in schema["components"]["schemas"]
    assert "Evidence" not in schema["components"]["schemas"]
    assert set(schema["components"]["schemas"]["PublicFortuneResponse"]["properties"]) == {
        "content", "interpretation", "result"
    }


def test_available_catalogs_contain_useful_inputs_and_no_internal_records():
    app = create_app(Settings(_env_file=None, api_key=None, openai_api_key=None, openai_model=""))
    with TestClient(app) as client:
        for path in ("/v1/fortunes", "/v1/un-services"):
            response = client.get(path)
            assert response.status_code == 200
            data = response.json()
            assert data["items"]
            assert_public_payload(data)
            for item in data["items"]:
                assert set(item) == {
                    "id", "name", "path", "requires_birth", "requires_partner", "calculation_only",
                    "parameter_examples", "parameter_help"
                }
        for path in ("/v1/asp-services", "/v1/source-data", "/v1/restored-data"):
            assert client.get(path).status_code == 404


def test_public_profile_parameter_name_preserves_the_calculation():
    body = {
        "birth": BIRTH, "target_date": "2027-01-01", "include_ai": False,
        "parameters": {"source_profile": "asp_original_unconverted"}
    }
    baseline = analyze_service("loveunse-flower", ServiceRequest(**body))
    assert baseline.evidence
    app = create_app(Settings(_env_file=None, api_key=None, openai_api_key=None, openai_model=""))
    with TestClient(app) as client:
        body["parameters"] = {"birth_profile": "as_entered"}
        response = client.post("/v1/un/loveunse-flower", json=body)
        assert response.status_code == 200, response.text
        assert_public_payload(response.json())
        legacy = client.post("/v1/un/loveunse-flower", json={
            **body, "parameters": {"source_profile": "asp_original_unconverted"}
        })
        assert legacy.status_code == 200
        assert response.json() == legacy.json()


def test_internal_section_instructions_become_readable_headings_in_public_prose():
    internal = analyze_service("loveunse-lotto", ServiceRequest(
        birth=BIRTH, target_date="2027-01-01", include_ai=False
    ))
    value = Interpretation(
        summary="생활 계획을 정리해 보세요.",
        sections=[{
            "target_id": target.id, "topic": target.topic, "text": "작은 목표를 살펴보세요.",
            "evidence_ids": target.evidence_ids
        } for target in internal.narrative_contract],
        practical_advice=["예산을 정해 보세요."]
    )
    before = deepcopy(value.model_dump(mode="json"))
    result = service_response(internal, value).model_dump(mode="json")
    assert_public_payload(result)
    for section in result["interpretation"]["sections"]:
        assert section["topic"] in result["content"]
        assert section["text"] in result["content"]
    assert value.model_dump(mode="json") == before
    assert value.sections[0].topic not in result["content"]
