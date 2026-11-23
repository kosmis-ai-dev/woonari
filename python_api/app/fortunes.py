"""CR-001 / T-002: original ASP decisions first; replace narrative lookup only."""

from datetime import timedelta
from math import ceil, pi, sin

from app.calendar import calculate_saju, day_ganji, solar_birth
from app.errors import DomainError
from app.legacy_inline import BIO_MENT, WEEK_DESC
from app.models import Analysis, Evidence, FortuneKind, FortuneRequest, NarrativeTarget
from app.rules import GANJI, daily_ten_god, legacy_scores, life_stage

CATALOG = {
    FortuneKind.daily: ("오늘의 운세", "old/unse/todayluck/main_end.asp"),
    FortuneKind.weekly: ("주간 운세", "old/unse/weekluck/main_end.asp"),
    FortuneKind.monthly: ("월간 운세", "old/unse/monthluck/main_end.asp"),
    FortuneKind.yearly: ("연간 운세", "old/unse/2014yearluck/main_end.asp"),
    FortuneKind.lifetime: ("평생 사주", "old/unse/lifeluck/main_end.asp"),
    FortuneKind.wealth: ("재물운", "old/unse/moneyluck/main_end.asp"),
    FortuneKind.career: ("직업운", "old/unse/carrerluck/main_end.asp"),
    FortuneKind.love: ("연애운", "old/unse/loveluck/main_end.asp"),
    FortuneKind.compatibility: ("궁합", "old/unse/fatewedluck/main_end.asp"),
    FortuneKind.biorhythm: ("바이오리듬", "old/unse/bioluck/main_end.asp"),
}

# Display the commercial service's actual name. Keep CATALOG's interpretation
# focus unchanged so a documentation update cannot change the AI contract.
SOURCE_SERVICE_NAMES = {
    FortuneKind.daily: "오늘의 운세",
    FortuneKind.weekly: "이번주 운세",
    FortuneKind.monthly: "이달의 운세",
    FortuneKind.yearly: "2014 도통비결 (연간 운세)",
    FortuneKind.lifetime: "평생운세",
    FortuneKind.wealth: "명품 평생재물운",
    FortuneKind.career: "나에게 맞는 직업",
    FortuneKind.love: "러브 어드바이스",
    FortuneKind.compatibility: "숙명의 궁합",
    FortuneKind.biorhythm: "바이오리듬",
}


def catalog():
    result = []
    for kind, (name, source) in CATALOG.items():
        dependent = kind in {FortuneKind.yearly, FortuneKind.career, FortuneKind.compatibility}
        result.append(
            {
                "id": kind.value,
                "name": SOURCE_SERVICE_NAMES[kind].replace("운세", "un"),
                "original_name": SOURCE_SERVICE_NAMES[kind],
                "category_name": name.replace("운세", "un"),
                "method": "asp-commercial",
                "legacy_reference": source,
                "requires_partner": kind == FortuneKind.compatibility,
                "readiness": "requires-original-dependency" if dependent else "ported",
                "narrative_only_ai": True,
                "required_inputs": ["career_category"] if kind == FortuneKind.career else [],
                "supported_target_years": list(range(2001, 2015))
                if kind == FortuneKind.yearly
                else None,
            }
        )
    return result


def _relation(master, gz):
    return {
        "pillar": gz,
        "stem_ten_god": daily_ten_god(master, gz[0]),
        "branch_ten_god": daily_ten_god(master, gz[1]),
        "life_stage": life_stage(master, gz[1]),
    }


def _daily_evidence(master, gender, value, *, temp_chk=None):
    gz = day_ganji(value)
    scores = legacy_scores(master, gz, gender, temp_chk=temp_chk)
    return Evidence(
        id=f"day-{value.isoformat()}",
        topic="daily",
        facts={
            "date": value.isoformat(),
            **_relation(master, gz),
            "tempChk": (
                life_stage(master, gz[1]) in {"사", "묘", "절"} if temp_chk is None else temp_chk
            ),
            "scores": [s.model_dump() for s in scores],
        },
        source="function/function.asp + function/valueDef.asp",
    ), scores


def _week_stars(total):
    # Exact source comparisons, including the unhandled threshold gaps.
    if total <= 42 * 8:
        return 0
    for low, high, stars in ((43, 46, 1), (47, 54, 2), (55, 60, 3), (61, 66, 4)):
        if low * 8 <= total <= high * 8:
            return stars
    return 5


def _week_grade(average):
    if average >= 61:
        return "very_good", 5
    if 55 <= average <= 60:
        return "effort", 4
    if 47 <= average <= 54:
        return "act", 3
    if 43 <= average <= 46:
        return "review", 2
    return "prepare", 1


def _selector(id, table, where, columns, purpose):
    return {"id": id, "table": table, "where": where, "columns": columns, "purpose": purpose}


def _attach_decision(decision, evidence):
    facts_id = "legacy-decision"
    evidence.append(
        Evidence(
            id=facts_id, topic="legacy_decision", facts=decision["facts"], source=decision["source"]
        )
    )
    selectors = decision.get("selectors", [])
    targets = []
    unresolved = decision.get("unresolved", [])
    for selector in selectors:
        evidence_id = f"lookup-{selector['id']}"
        evidence.append(
            Evidence(
                id=evidence_id,
                topic="legacy_text_selector",
                facts=selector,
                source=decision["source"],
            )
        )
        # Calculation queries are retained as provenance, never assigned to the AI.
        if selector.get("role") == "calculation" or selector.get("narrative") is False:
            continue
        if selector.get("unresolved") or not selector.get("columns"):
            continue
        if unresolved:
            # Missing source judgments mean even text selection is not final.
            # Keep selectors in provenance, but publish no AI writing contract.
            continue
        for column in selector["columns"]:
            target_id = f"{selector['id']}.{column}"
            targets.append(
                NarrativeTarget(
                    id=target_id,
                    topic=selector.get("purpose", column),
                    output_field=column,
                    evidence_ids=[facts_id, evidence_id, "natal"],
                    constraints=[
                        "원본 선택키·분기·수치를 변경하지 않는다.",
                        "DB 원문을 복원했다고 말하지 않고 제공된 판정 근거로만 문장화한다.",
                    ],
                )
            )
    return selectors, targets, unresolved


def analyze(kind: FortuneKind, request: FortuneRequest) -> Analysis:
    if (kind == FortuneKind.compatibility) != (request.partner is not None):
        raise DomainError("invalid_partner", "궁합에만 partner가 필수입니다.")
    if kind != FortuneKind.career and request.career_category is not None:
        raise DomainError("invalid_career_category", "career_category는 직업운에서만 사용합니다.")
    born = solar_birth(request.birth)
    if born.date() > request.target_date:
        raise DomainError("target_before_birth", "조회 날짜는 출생일 이후여야 합니다.")
    profile = (
        "today_inline"
        if kind in {FortuneKind.daily, FortuneKind.weekly, FortuneKind.monthly}
        else "dotong"
    )
    saju = calculate_saju(request.birth, profile=profile)
    master = saju.day_master
    start = end = request.target_date
    evidence = [
        Evidence(
            id="natal",
            topic="natal",
            source="ASP CalcSaju source profile + script.sql tb_manse database",
            facts={
                "pillars": {k: p.model_dump() for k, p in saju.pillars.items()},
                "day_master": master,
                "elements": saju.elements,
                "calculation_profile": profile,
            },
        )
    ]
    scores, notes, targets, selectors, unresolved = [], [], [], [], []
    partner = None
    source = CATALOG[kind][1]
    if kind == FortuneKind.daily:
        day, scores = _daily_evidence(master, request.birth.gender, request.target_date)
        evidence.append(day)
        number = GANJI.index(day_ganji(request.target_date))
        selectors = [
            _selector(
                name,
                "dayfortune",
                {"memno": int(saju.legacy_memno[0]), "num": (number + offset) % 60},
                ["contents"],
                label,
            )
            for name, offset, label in (
                ("prevcontent", -1, "어제의 운세"),
                ("todaycontent", 0, "오늘의 운세"),
                ("nextcontent", 1, "내일의 운세"),
            )
        ]
        _, targets, _ = _attach_decision(
            {
                "source": source,
                "facts": {
                    "memno": int(saju.legacy_memno[0]),
                    "num": number,
                    "n_num": (number + 1) % 60,
                    "p_num": (number - 1) % 60,
                    "eight_scores": [s.model_dump() for s in scores],
                },
                "selectors": selectors,
            },
            evidence,
        )
    elif kind == FortuneKind.weekly:
        start = request.target_date - timedelta(days=(request.target_date.weekday() + 1) % 7)
        end = start + timedelta(days=6)
        days, sticky = [], False
        for i in range(7):
            value = start + timedelta(days=i)
            gz = day_ganji(value)
            # ASP only assigns OK, never clears tempChk inside the seven-day loop.
            sticky = sticky or life_stage(master, gz[1]) in {"사", "묘", "절"}
            item, current = _daily_evidence(master, request.birth.gender, value, temp_chk=sticky)
            evidence.append(item)
            total = sum(s.favorable for s in current)
            days.append(
                {
                    "date": value.isoformat(),
                    "emScore": total,
                    "stars": _week_stars(total),
                    "tempChk": sticky,
                }
            )
        total_score = sum(day["emScore"] for day in days)
        average = round(total_score / 5600 * 100)  # VBScript Round: ties to even.
        grade, stars = _week_grade(average)
        evidence.append(
            Evidence(
                id="week-summary",
                topic="weekly",
                source=source + ":153-252",
                facts={
                    "days": days,
                    "totalMeScore": total_score,
                    "totalScore": 5600,
                    "scoreAverage": average,
                    "grade": grade,
                    "stars": stars,
                    "original_inline_anchor": WEEK_DESC[grade],
                    "state_scope": "tempChk persists within this request's week only",
                },
            )
        )
        targets = [
            NarrativeTarget(
                id="weekDesc",
                topic="주간 총평",
                output_field="weekDesc",
                evidence_ids=["week-summary"],
                constraints=[f"원본 주간 등급 {grade}, 별 {stars}개를 유지한다."],
            )
        ]
        notes.append("원본 tempChk 주간 누적 동작과 별점 비교식을 그대로 보존합니다.")
    elif kind in {FortuneKind.monthly, FortuneKind.yearly}:
        from app.legacy_periods import decide_period

        decision = decide_period(kind.value, request, saju)
        start, end = decision.get("period_start", start), decision.get("period_end", end)
        selectors, targets, unresolved = _attach_decision(decision, evidence)
        notes.extend(decision.get("notes", []))
    elif kind in {FortuneKind.lifetime, FortuneKind.wealth}:
        from app.legacy_life_wealth import decide_life_wealth
        from app.source_archive import resolve_decision

        decision = decide_life_wealth(kind.value, request, saju)
        decision = resolve_decision(kind.value, decision)
        selectors, targets, unresolved = _attach_decision(decision, evidence)
        notes.extend(decision.get("notes", []))
    elif kind in {FortuneKind.career, FortuneKind.love, FortuneKind.compatibility}:
        from app.legacy_relationships import decide_relationship

        if request.partner is not None:
            if solar_birth(request.partner).date() > request.target_date:
                raise DomainError("target_before_birth", "상대방 출생일 이후 날짜를 입력하세요.")
            partner = calculate_saju(request.partner, profile="dotong")
        decision = decide_relationship(kind.value, request, saju, partner)
        selectors, targets, unresolved = _attach_decision(decision, evidence)
        notes.extend(decision.get("notes", []))
    elif kind == FortuneKind.biorhythm:
        elapsed = (request.target_date - born.date()).days
        rhythms, marks = [], []
        for label, cycle in (("physical", 23), ("emotional", 28), ("intellectual", 33)):
            phase = elapsed % cycle
            mark = 1 if phase in {0, ceil(cycle / 2)} else 2 if phase < cycle / 2 else 3
            marks.append(mark)
            rhythms.append(
                {
                    "key": label,
                    "cycle_days": cycle,
                    "phase": phase,
                    "state": {1: "critical", 2: "high", 3: "low"}[mark],
                    "value": round(sin(elapsed / cycle * 2 * pi) * 100, 4),
                }
            )
        check = marks[0] * 100 + marks[1] * 10 + marks[2]
        ment_index = (marks[0] - 1) * 9 + (marks[1] - 1) * 3 + marks[2]
        evidence.append(
            Evidence(
                id="biorhythm",
                topic="biorhythm",
                source=source + ":335-453",
                facts={
                    "elapsed_days": elapsed,
                    "rhythms": rhythms,
                    "check": check,
                    "ment_index": ment_index,
                    "original_inline_anchor": BIO_MENT[ment_index],
                },
            )
        )
        targets = [
            NarrativeTarget(
                id="bioment",
                topic="바이오리듬 해석",
                output_field="bioment",
                evidence_ids=["biorhythm"],
                constraints=[
                    "원본 주기 상태/멘트분류를 유지하되 건강·사고의 실제 확률로 단정하지 않는다."
                ],
            )
        ]
    return Analysis(
        kind=kind,
        target_date=request.target_date,
        period_start=start,
        period_end=end,
        saju=saju,
        partner_saju=partner,
        scores=scores,
        evidence=evidence,
        method="asp-commercial",
        notes=notes,
        source_file=source,
        selectors=selectors,
        narrative_contract=targets,
        unresolved_dependencies=unresolved,
        ready_for_ai=not unresolved and bool(targets),
    )
