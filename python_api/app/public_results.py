"""CR-021 / T-041: project internal calculations onto public result schemas.

The internal calculation and interpretation contracts remain available to the
engine. Only computed values and the validated prose cross this boundary.
"""

import math
import re
from datetime import date, datetime
from typing import Any

from app.errors import DomainError
from app.models import Analysis, Interpretation, SajuResult
from app.public_models import (
    CalculationResult,
    FortuneResult,
    PublicFortuneResponse,
    PublicInterpretation,
    PublicSajuResult,
)
from app.service_models import ServiceAnalysis
from app.service_offerings import SERVICE_OFFERINGS

_OMIT = object()
_INTERNAL_KEY = re.compile(r"(?:^|_)(?:asp|source|original|legacy|provenance)(?:_|$)", re.IGNORECASE)
_INTERNAL_TEXT = re.compile(
    r"\bASP\b|\.asp\b|\.py\b|\.sql\b|\bVBScript\b|\bVB_Empty\b|"
    r"\bsource[_ -]|\blegacy[_ -]|\bCR-\d+\b|\bT-\d+\b|"
    r"원본|이식|출처|소스|미확보|미검증|전환 완료|동일성|해시|조회키|선택키|"
    r"(?:^|\s)(?:app|old|function|python_api)/",
    re.IGNORECASE
)
_PROSE_INTERNAL_TEXT = re.compile(
    r"\bASP\b|\.asp\b|\.py\b|\.sql\b|\bVBScript\b|\bVB_Empty\b|"
    r"\bsource[_ -]|\blegacy[_ -]|\bCR-\d+\b|\bT-\d+\b|"
    r"이식 완료|소스 코드|원본\s*(?:코드|판정|로직|자료|데이터|서비스|출력|선택|조회)|출처 경로|"
    r"(?:^|\s)(?:app|old|function|python_api)/",
    re.IGNORECASE
)
_TECHNICAL_KEYS = {
    "method", "policy", "notes", "helper", "constraints", "narrative_contract",
    "narrative_policy", "unresolved_dependencies", "ready_for_ai", "calculation_only",
    "calculation_profile", "lunar_correction_version", "state_scope", "tempChk",
    "bindings", "output_bindings", "output_fields", "output_order", "output_variable",
    "excluded_non_narrative", "text_selection_keys", "selector_id", "selector_count",
    "selector_number", "selector_is_score", "selectors", "table", "tables", "where",
    "columns", "column", "result_column", "selected_column", "purpose", "role",
    "narrative", "interpretation_limit", "interpretation_basis", "missing_value_policy",
    "text_projection_profile", "input_privacy", "alert_semantics", "randomness_note",
    "memno", "dokebi", "ilgan_memno_digit", "num", "n_num", "p_num", "eight_scores",
    "gender_field_suffix", "mybar", "check", "ment_index", "year_rule",
    "target_date_replaces_server_Date", "replacement_manse", "calendar_replacement",
    "odd_division_increment_applied", "basic_calendar_adapter", "partner_basic_calendar_adapter",
    "shared_saju_preamble_used", "saju_or_major_luck_equivalence_claimed",
    "calendar_argument", "calendar_action", "option_name_effect", "helper_sex_code",
    "active_codes", "ratings", "unavailable", "scope", "period_basis", "end_semantics"
}
_TOPICS = {
    "legacy_decision": "계산 결과",
    "natal": "사주",
    "daily": "일진",
    "weekly": "주간 결과",
    "monthly": "월간 결과",
    "annual_saju_context": "연간 사주 관계",
    "biorhythm": "바이오리듬"
}


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if not isinstance(key, str):
                continue
            if key == "legacy_age":
                key = "age"
            elif key == "verified_source_facts":
                # Flower/stone names, symbols and other known facts are data.
                key, child = "classification", child.get("values", {}) if isinstance(child, dict) else {}
            elif key in _TECHNICAL_KEYS or _INTERNAL_KEY.search(key):
                continue
            if key == "major_luck" and isinstance(child, dict) and not child.get("available"):
                continue
            cleaned = _clean(child)
            if cleaned is not _OMIT:
                result[key] = cleaned
        return result if result else _OMIT
    if isinstance(value, (list, tuple)):
        result = []
        for child in value:
            cleaned = _clean(child)
            if cleaned is not _OMIT:
                result.append(cleaned)
        return result
    if isinstance(value, str):
        return _OMIT if _INTERNAL_TEXT.search(value) else value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    return _OMIT


def clean_result_values(values: dict) -> dict:
    """Return only serializable result values without implementation metadata."""
    cleaned = _clean(values)
    return {} if cleaned is _OMIT else cleaned


def saju_result(value: SajuResult) -> PublicSajuResult:
    return PublicSajuResult(
        solar_birth=value.solar_birth,
        lunar_birth=value.lunar_birth,
        pillars=value.pillars,
        day_master=value.day_master,
        elements=value.elements,
        solar_term_window=clean_result_values(value.solar_term_window)
    )


def _interpretation(value: Interpretation | None) -> PublicInterpretation | None:
    if value is None:
        return None
    prose = [value.summary, *value.practical_advice]
    prose.extend(section.text for section in value.sections)
    if any(_PROSE_INTERNAL_TEXT.search(text) for text in prose):
        # Do not silently alter a validated interpretation or return developer text.
        raise DomainError("invalid_interpretation", "un 본문을 생성하지 못했습니다.", 502)
    return PublicInterpretation(
        summary=value.summary,
        sections=[
            {
                "topic": f"항목별 풀이 {index}" if _INTERNAL_TEXT.search(section.topic) else section.topic,
                "text": section.text
            }
            for index, section in enumerate(value.sections, 1)
        ],
        practical_advice=value.practical_advice
    )


def _response(
    analysis: Analysis | ServiceAnalysis,
    interpretation: Interpretation | None,
    *,
    service_id: str | None = None,
    title: str | None = None
) -> PublicFortuneResponse:
    calculations = []
    for evidence in analysis.evidence:
        # Saju is already exposed as typed data. Lookup contracts are not results.
        if evidence.topic in {"natal", "legacy_text_selector"}:
            continue
        values = clean_result_values(evidence.facts)
        if values:
            topic = _TOPICS.get(evidence.topic, evidence.topic)
            if _INTERNAL_TEXT.search(topic):
                topic = "계산 결과"
            calculations.append(CalculationResult(topic=topic, values=values))
    public_interpretation = _interpretation(interpretation)
    content = None
    if public_interpretation is not None:
        paragraphs = [public_interpretation.summary]
        paragraphs.extend(f"{section.topic}\n{section.text}" for section in public_interpretation.sections)
        paragraphs.append("실천 조언\n" + "\n".join(f"- {item}" for item in public_interpretation.practical_advice))
        content = "\n\n".join(paragraphs)
    return PublicFortuneResponse(
        content=content,
        interpretation=public_interpretation,
        result=FortuneResult(
            kind=str(analysis.kind), title=title, service_id=service_id,
            target_date=analysis.target_date, period_start=analysis.period_start,
            period_end=analysis.period_end,
            saju=saju_result(analysis.saju) if analysis.saju is not None else None,
            partner_saju=saju_result(analysis.partner_saju) if analysis.partner_saju is not None else None,
            scores=analysis.scores,
            calculations=calculations
        )
    )


def fortune_response(
    analysis: Analysis,
    interpretation: Interpretation | None = None
) -> PublicFortuneResponse:
    offering = SERVICE_OFFERINGS.get(f"/v1/fortunes/{analysis.kind}")
    return _response(analysis, interpretation, title=offering[0] if offering else None)


def service_response(
    analysis: ServiceAnalysis,
    interpretation: Interpretation | None = None
) -> PublicFortuneResponse:
    return _response(
        analysis, interpretation, service_id=analysis.service_id,
        title=analysis.title.replace("운세", "un")
    )
