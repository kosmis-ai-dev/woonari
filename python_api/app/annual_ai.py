"""CR-018 / T-038: annual prose grounded in the existing calendar and saju.

This is an AI interpretation mode, not a reconstruction of yearfortune scores.
The civil-year period and July reference day are explicit product conventions.
"""

from datetime import date, datetime

from app.calendar import KST, period_pillars, pillar
from app.models import Analysis, Evidence, FortuneKind, FortuneRequest, NarrativeTarget, SajuResult
from app.rules import ten_god

METHOD = "asp-saju-ai-yearly-v1"
TOPICS = (
    ("overview", "연간 총운"),
    ("career", "직장·사업·학업"),
    ("wealth", "재물·생활 관리"),
    ("relationships", "연애·가족·인간관계"),
    ("wellbeing", "건강·생활 습관"),
    ("movement", "이동·변화"),
    ("preparation", "올해의 준비와 실천")
)


def analyze_yearly(request: FortuneRequest, saju: SajuResult, natal: list[Evidence]) -> Analysis:
    year = request.target_date.year
    reference = datetime(year, 7, 1, 12, tzinfo=KST)
    year_pillar = period_pillars(reference)["year"]
    annual = Evidence(
        id="annual-context",
        topic="annual_saju_context",
        source="tb_manse + app.calendar.period_pillars/pillar + app.rules.ten_god; CR-018",
        facts={
            "year": year,
            "reference_date": reference.date().isoformat(),
            "period_basis": "양력 1월 1일~12월 31일 전체 안내; 연간 대표 간지는 해당 연도 입춘 이후 7월 1일 12시의 기존 만세력 계산값",
            "year_pillar": pillar(year_pillar, saju.day_master).model_dump(),
            "relations_to_natal_stems": {
                name: ten_god(value.stem, year_pillar[0])
                for name, value in saju.pillars.items()
            },
            "interpretation_basis": "사주·대상 연도 관계에 대한 AI의 전통적 상징 해석; 기존 연간 DB 판정 재현 아님",
            "ratings": {"stars": None, "scores": None, "status": "not_provided"},
            "unavailable": ["월별 길흉 판정", "용신·신살·대운의 연간 판정", "별점·점수·부적"],
            "scope": "계산된 간지·십성·오행·십이운성을 설명하는 연간 해석. 실제 사건·질병·투자 성과의 확정 예측 아님"
        }
    )
    targets = [
        NarrativeTarget(
            id=f"annual.{key}", topic=topic, output_field=key,
            evidence_ids=["natal", annual.id],
            constraints=[
                f"{year}년 전체에 대해 개인 사주와 연도 근거를 연결해 해석한다.",
                "본문은 AI의 해석이며 원본 DB 판정·확정된 길흉으로 표현하지 않는다.",
                "별점·점수·확률·부적·근거 없는 월별 길흉을 만들지 않는다.",
                "건강은 생활 습관 조언, 재물은 일반적인 지출·계획 조언으로 설명한다."
            ]
        )
        for key, topic in TOPICS
    ]
    return Analysis(
        kind=FortuneKind.yearly, target_date=request.target_date,
        period_start=date(year, 1, 1), period_end=date(year, 12, 31),
        saju=saju, scores=[], evidence=[*natal, annual], method=METHOD,
        source_file="app/annual_ai.py; 사주 계산은 기존 ASP dotong 프로필 유지",
        selectors=[], narrative_contract=targets, unresolved_dependencies=[], ready_for_ai=True,
        notes=[
            "연간 운세 DB 본문·별점·점수 없이 개인 사주와 대상 연도 근거로 AI가 해석합니다.",
            "별점·점수·부적은 미제공입니다. 기존 상용 연간 DB 결과와 동일하다고 주장하지 않습니다.",
            "양력 연도 전체 안내이며 절입 기준 월별 예측을 제공하지 않습니다."
        ]
    )
