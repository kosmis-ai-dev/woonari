"""CR-013 / T-028: constrain prose to available facts without changing ASP decisions.

The failure phrases are short excerpts observed during paid smoke review.
These regressions use calculated fixture analyses and never call a model.
"""

from datetime import date

import pytest

from app.ai import interpretation_payload, validate_interpretation
from app.errors import DomainError
from app.fortunes import analyze
from app.models import Evidence, FortuneKind, FortuneRequest, Interpretation, NarrativeTarget
from app.service_engine import analyze_service
from app.service_models import ServiceAnalysis, ServiceRequest

BIRTH = {"year": 1990, "month": 5, "day": 17, "hour": 14, "minute": 30, "gender": "male"}
DAY = "2026-11-19"


@pytest.fixture(scope="module")
def analyses():
    body = {"birth": BIRTH, "target_date": DAY, "include_ai": False}
    return {
        "daily": analyze(FortuneKind.daily, FortuneRequest(**body)),
        "lifetime": analyze(FortuneKind.lifetime, FortuneRequest(**body)),
        "analysisluck": analyze_service("analysisluck", ServiceRequest(**body)),
    }


def human_interpretation(analysis):
    return Interpretation(
        summary="제공된 근거의 범위에서 현재 상황을 차분하게 살펴보세요.",
        sections=[{
            "target_id": target.id, "topic": target.topic,
            "text": "사람의 성향을 단정하기보다 대화를 나누며 직접 확인해 보세요.",
            "evidence_ids": target.evidence_ids,
        } for target in analysis.narrative_contract],
        practical_advice=["중요한 결정 전에 확인할 정보를 정리해 보세요."],
    )


def test_opaque_arithmetic_keys_allow_general_advice_not_personality_judgement(analyses):
    analysis = analyses["analysisluck"]
    assert analysis.saju is None and not analysis.scores and analysis.ready_for_ai
    payload = interpretation_payload(analysis)
    policy = payload["writing_policy"]
    assert payload["prompt_version"] == "fortune-ko-v6-source-definitions"
    assert policy["overall_mode"] == "general_advice_only"
    assert policy["targets"] == {
        target.id: "general_advice_only" for target in analysis.narrative_contract
    }


def test_daily_other_days_do_not_inherit_the_target_dates_judgement(analyses):
    analysis = analyses["daily"]
    policy = interpretation_payload(analysis)["writing_policy"]
    assert policy["overall_mode"] == "grounded_interpretation"
    assert policy["targets"] == {
        "prevcontent.contents": "general_natal_advice_no_day_judgement",
        "todaycontent.contents": "grounded_interpretation",
        "nextcontent.contents": "general_natal_advice_no_day_judgement",
    }


def test_dangsaju_period_codes_do_not_establish_life_period_fortunes(analyses):
    analysis = analyses["lifetime"]
    policy = interpretation_payload(analysis)["writing_policy"]
    assert policy["overall_mode"] == "grounded_interpretation"
    limited = {
        "lifetime-dangsaju-early.desc1",
        "lifetime-dangsaju-middle.desc2",
        "lifetime-dangsaju-late.desc3",
    }
    assert len(analysis.narrative_contract) == 13
    assert policy["targets"] == {
        target.id: "general_advice_only" if target.id in limited else "grounded_interpretation"
        for target in analysis.narrative_contract
    }


def test_original_inline_text_can_ground_a_service_without_saju_or_scores():
    analysis = ServiceAnalysis(
        service_id="fixture-inline", kind="fixture-inline", title="원본 문장 사례",
        target_date=date(2026, 11, 19), period_start=date(2026, 11, 19),
        period_end=date(2026, 11, 19), ready_for_ai=True,
        evidence=[Evidence(
            id="source-inline", topic="original_inline", source="frozen-source-fixture",
            facts={"original_inline_anchor": "서두르지 말고 차분히 준비하는 편이 좋습니다."},
        )],
        narrative_contract=[NarrativeTarget(
            id="message.text", topic="현재의 조언", output_field="text",
            evidence_ids=["source-inline"], constraints=["원본 문장의 의미를 유지합니다."],
        )],
    )
    assert analysis.saju is None and not analysis.scores
    policy = interpretation_payload(analysis)["writing_policy"]
    assert policy["overall_mode"] == "grounded_interpretation"
    assert policy["targets"] == {"message.text": "grounded_interpretation"}


@pytest.mark.parametrize("kind", ["daily", "lifetime", "analysisluck"])
def test_writing_policy_does_not_change_original_analysis(analyses, kind):
    analysis = analyses[kind]
    before = analysis.model_dump(mode="json")
    payload = interpretation_payload(analysis)
    assert payload["writing_policy"]["targets"]
    assert analysis.model_dump(mode="json") == before


@pytest.mark.parametrize("text", [
    "사교성 항목은 Mod144 식에서도 원본 기준이 적용되었습니다.",
    "원본 intMyDee(Mod12) 기준이 적용되었습니다.",
    "선택키 12번으로 도출되었습니다.",
    "선택 키 12번으로 도출되었습니다.",
    "십육궁 코드 3번에 해당합니다.",
    "초년 당사주 코드 'c'로 판정되었습니다.",
    '중년 당사주 코드 "a"로 판정되었습니다.',
    "식신 코드 3번에 해당하는 재물운입니다.",
])
def test_observed_internal_formula_and_code_disclosures_are_rejected(analyses, text):
    analysis = analyses["daily"]
    value = human_interpretation(analysis)
    value.sections[0].text = text
    with pytest.raises(DomainError) as error:
        validate_interpretation(value, analysis)
    assert error.value.code == "ai_internal_terms"
    assert error.value.status == 502


@pytest.mark.parametrize("location", ["summary", "advice"])
def test_internal_codes_are_blocked_outside_sections_too(analyses, location):
    analysis = analyses["daily"]
    value = human_interpretation(analysis)
    if location == "summary":
        value.summary = "선택키 12번으로 도출되었습니다."
    else:
        value.practical_advice = ["당사주 코드 'a'를 참고하세요."]
    with pytest.raises(DomainError) as error:
        validate_interpretation(value, analysis)
    assert error.value.code == "ai_internal_terms"


@pytest.mark.parametrize("kind", ["daily", "lifetime", "analysisluck"])
def test_human_facing_non_assertive_prose_still_passes_contract_validation(analyses, kind):
    analysis = analyses[kind]
    value = human_interpretation(analysis)
    assert validate_interpretation(value, analysis) == value


def test_verified_definition_anchor_only_grounds_its_matching_output(analyses):
    analysis = analyses["analysisluck"].model_copy(deep=True)
    selector = analysis.selectors[0]
    column = selector["columns"][0]
    selector.update(source_data_status="verified", source_anchors={
        column: {"scope": "source_definition", "text": "대화와 관찰을 통해 서로 이해해 보세요."},
    })
    policy = interpretation_payload(analysis)["writing_policy"]
    assert policy["overall_mode"] == "general_advice_only"
    matching = f"{selector['id']}.{column}"
    assert policy["targets"][matching] == "grounded_source_definition"
    assert all(mode == "general_advice_only" for key, mode in policy["targets"].items()
               if key != matching)


@pytest.mark.parametrize("status", ["unverified", "missing", "unavailable"])
def test_unverified_source_text_cannot_expand_writing_scope(analyses, status):
    analysis = analyses["analysisluck"].model_copy(deep=True)
    selector = analysis.selectors[0]
    selector.update(source_data_status=status, source_anchors={selector["columns"][0]: {
        "scope": "source_definition", "text": "인위적으로 입력한 자료",
    }})
    assert set(interpretation_payload(analysis)["writing_policy"]["targets"].values()) == {
        "general_advice_only",
    }


@pytest.mark.parametrize("status", ["verified", "missing_source_row"])
def test_unsafe_source_scope_stays_general_even_when_saju_is_present(analyses, status):
    analysis = analyses["lifetime"].model_copy(deep=True)
    target = analysis.narrative_contract[0]
    selector = next(s for s in analysis.selectors
                    if target.id == f"{s['id']}.{target.output_field}")
    selector.update(source_data_status=status, source_anchors={target.output_field: {
        "scope": "general_advice_only",
    }})
    policy = interpretation_payload(analysis)["writing_policy"]
    assert policy["overall_mode"] == "grounded_interpretation"
    assert policy["targets"][target.id] == "general_advice_only"
