"""CR-018: annual AI receives personal/year facts without fortune table rows."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.ai import interpretation_payload, validate_interpretation
from app.annual_ai import METHOD
from app.config import Settings
from app.errors import DomainError
from app.fortunes import analyze
from app.main import create_app, get_interpreter
from app.models import FortuneKind, FortuneRequest, Interpretation

BIRTH = {"year": 1974, "month": 3, "day": 2, "hour": 8, "minute": 30, "gender": "male"}


def request(target="2027-01-01", birth=None):
    return FortuneRequest(birth=birth or BIRTH, target_date=target, include_ai=False)


def response_for(analysis):
    return Interpretation(
        summary="사주와 해당 연도의 관계를 바탕으로 계획을 정리해 보세요.",
        sections=[{
            "target_id": t.id, "topic": t.topic,
            "text": "주어진 사주와 연도 관계를 살펴 자신의 생활에 맞게 준비해 보세요.",
            "evidence_ids": t.evidence_ids
        } for t in analysis.narrative_contract],
        practical_advice=["생활 계획을 기록해 보세요."]
    )


def test_2027_has_personal_and_yearly_grounding_without_fortune_rows(monkeypatch):
    monkeypatch.setattr("app.source_archive.resolve_decision", lambda *a: pytest.fail("annual must not read fortune archive"))
    result = analyze(FortuneKind.yearly, request())
    annual = result.evidence[-1].facts
    assert result.method == METHOD and result.ready_for_ai
    assert result.selectors == [] and result.unresolved_dependencies == []
    assert result.scores == []
    assert annual["ratings"] == {"stars": None, "scores": None, "status": "not_provided"}
    assert annual["year_pillar"]["hanja"] == "丁未"
    assert annual["reference_date"] == "2027-07-01"
    assert set(annual["relations_to_natal_stems"]) == {"year", "month", "day", "hour"}
    assert result.period_start.isoformat() == "2027-01-01"
    assert result.period_end.isoformat() == "2027-12-31"
    assert len(result.narrative_contract) == 7
    payload = interpretation_payload(result)
    assert payload["writing_policy"]["overall_mode"] == "annual_saju_interpretation"
    assert set(payload["writing_policy"]["targets"].values()) == {"annual_saju_interpretation"}
    assert all(set(t.evidence_ids) == {"natal", "annual-context"} for t in result.narrative_contract)
    assert payload["evidence"][0]["facts"]["pillars"] == {
        name: value.model_dump() for name, value in result.saju.pillars.items()
    }


def test_civil_year_context_is_consistent_and_next_year_changes():
    january = analyze(FortuneKind.yearly, request())
    december = analyze(FortuneKind.yearly, request("2027-12-31"))
    next_year = analyze(FortuneKind.yearly, request("2028-01-01"))
    assert january.evidence == december.evidence
    assert next_year.evidence[-1].facts["year_pillar"]["hanja"] == "戊申"
    other = analyze(FortuneKind.yearly, request(birth={**BIRTH, "day": 3}))
    assert january.evidence[0].facts != other.evidence[0].facts
    assert january.evidence[-1].facts["relations_to_natal_stems"] != other.evidence[-1].facts["relations_to_natal_stems"]


@pytest.mark.parametrize("prose", ["올해는 85점입니다.", "별 4개입니다.", "좋은 흐름 ★★★★", "성공 가능성 90%입니다."])
def test_annual_model_cannot_supply_unrequested_ratings(prose):
    result = analyze(FortuneKind.yearly, request())
    value = response_for(result)
    value.summary = prose
    with pytest.raises(DomainError) as error:
        validate_interpretation(value, result)
    assert error.value.code == "ai_unrequested_rating"


def test_annual_model_requires_both_personal_and_year_evidence():
    result = analyze(FortuneKind.yearly, request())
    value = response_for(result)
    value.sections[0].evidence_ids = ["natal"]
    with pytest.raises(DomainError) as error:
        validate_interpretation(value, result)
    assert error.value.code == "ai_invalid_evidence"


@pytest.mark.parametrize("path", ["/v1/fortunes/yearly", "/v1/un/2014yearluck"])
def test_all_annual_aliases_generate_ai_from_identical_context(path):
    fake = SimpleNamespace(name="test", model="fixture", interpret=AsyncMock(side_effect=response_for), close=AsyncMock())
    app = create_app(Settings(_env_file=None, api_key=None, openai_api_key=None, openai_model=""))
    app.dependency_overrides[get_interpreter] = lambda: fake
    with TestClient(app) as client:
        body = {"birth": BIRTH, "target_date": "2027-01-01", "include_ai": False}
        if "/un/" in path:
            body["parameters"] = {}
        calculation = client.post(path, json=body)
        assert calculation.status_code == 200, calculation.text
        fake.interpret.assert_not_called()
        generated = client.post(path, json={**body, "include_ai": True})
        assert generated.status_code == 200, generated.text
        value = generated.json()
        assert value["content"] and len(value["interpretation"]["sections"]) == 7
        assert value["result"] == calculation.json()["result"]
        assert value["result"]["scores"] == []
        fake.interpret.assert_awaited_once()
