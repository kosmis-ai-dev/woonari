from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Birth(Model):
    model_config = ConfigDict(title="생년월일시와 성별")
    year: Annotated[
        int,
        Field(
            strict=True,
            ge=1900,
            le=2050,
            title="출생 연도",
            description="출생 연도입니다. 숫자 4자리로 입력합니다. 예: 1990",
            examples=[1990],
        ),
    ]
    month: Annotated[
        int,
        Field(
            strict=True,
            ge=1,
            le=12,
            title="출생 월",
            description="출생 월(1~12)입니다. 음력 생일은 calendar=lunar를 함께 지정합니다.",
            examples=[5],
        ),
    ]
    day: Annotated[
        int,
        Field(
            strict=True,
            ge=1,
            le=31,
            title="출생 일",
            description="출생 일입니다. 존재하지 않는 양력·음력 날짜는 거절합니다.",
            examples=[17],
        ),
    ]
    hour: Annotated[
        int,
        Field(
            strict=True,
            ge=0,
            le=23,
            title="출생 시",
            description="한국시간 기준 24시간제 시각(0~23)입니다. 예: 오전 8시=8, 오후 2시=14. 필수 입력입니다.",
            examples=[14],
        ),
    ]
    minute: Annotated[
        int,
        Field(
            strict=True,
            ge=0,
            le=59,
            title="출생 분",
            description="출생 시각의 분(0~59)입니다. 생략하면 0분입니다.",
            examples=[30],
        ),
    ] = 0
    calendar: Literal["solar", "lunar"] = Field(
        default="solar",
        title="양력·음력",
        description="solar=양력, lunar=음력입니다. 생일이 음력이면 lunar로 바꾸세요.",
    )
    leap_month: bool = Field(
        default=False,
        title="음력 윤달 여부",
        description="음력 윤달 생일만 true입니다. 양력 생일은 반드시 false로 둡니다.",
    )
    gender: Literal["male", "female"] = Field(
        title="성별", description="male=남성, female=여성입니다."
    )

    @model_validator(mode="after")
    def validate_date(self):
        if self.calendar == "solar":
            date(self.year, self.month, self.day)
            if self.leap_month:
                raise ValueError("양력 입력에는 leap_month를 사용할 수 없습니다.")
        return self


class SajuRequest(Model):
    model_config = ConfigDict(title="사주 계산 요청")
    birth: Birth = Field(
        title="사주를 계산할 사람", description="생년월일시·양력/음력·윤달·성별을 입력합니다."
    )
    calculation_profile: Literal["today_inline", "dotong"] = Field(
        default="dotong",
        title="사주 계산 기준",
        description="기본값 dotong을 사용하세요. today_inline은 오늘·주간·월간 un의 계산 기준입니다. 23:30 이후 시주 계산 방식이 다릅니다.",
    )


class FortuneKind(StrEnum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"
    lifetime = "lifetime"
    wealth = "wealth"
    love = "love"
    compatibility = "compatibility"
    biorhythm = "biorhythm"


class FortuneRequest(Model):
    model_config = ConfigDict(title="un 테스트 요청")
    birth: Birth = Field(
        title="본인 사주 입력", description="본인의 생년월일시·양력/음력·윤달·성별입니다."
    )
    target_date: date = Field(
        title="조회 기준 날짜",
        description="un을 확인할 양력 날짜입니다. YYYY-MM-DD 형식이며 출생일 이후여야 합니다. 주간·월간은 이 날짜가 속한 기간을 봅니다. 연간은 해당 양력 연도 전체를 해석하며 1900~2050년을 지원합니다.",
        examples=["2026-11-02"],
    )
    partner: Birth | None = Field(
        default=None,
        title="궁합 상대방 사주",
        description="궁합(compatibility)에만 필수입니다. 다른 un에서는 이 필드를 생략하거나 null로 둡니다.",
    )
    include_ai: bool = Field(
        default=True,
        title="AI 해석 포함 여부",
        description="true는 실제 AI un 본문을 생성합니다. 연간 un은 사주·연도 근거를 AI가 해석하며 별점/점수 없이 2027년도 지원합니다. 전용 AI 인증·모델 설정이 필요하며 false는 계산 근거만 확인합니다.",
    )

    @model_validator(mode="after")
    def validate_target(self):
        if not date(1900, 1, 1) <= self.target_date <= date(2050, 12, 31):
            raise ValueError("target_date 지원 범위는 1900-01-01 ~ 2050-12-31입니다.")
        return self


class Pillar(Model):
    hanja: str
    hangul: str
    stem: str
    branch: str
    stem_element: str
    branch_element: str
    stem_ten_god: str
    branch_ten_god: str
    life_stage: str


class CalendarPolicy(Model):
    version: str = "asp-manse-db-v4"
    lunar_correction_version: str = "lunar-leap-flags-v1"
    data_backend: str = "sqlite"
    calculation_profile: str = "today_inline"
    timezone: str = "UTC+09:00 (fixed)"
    solar_terms: str = "script.sql tb_manse div_name/div_hour/div_min (UTC+09:00)"
    lunar_calendar: str = "script.sql tb_manse + lunar-leap-flags-v1 윤달 표시 교정 10행"
    day_boundary: str = "00:30 이전은 전날 일주; 시주는 보정 전 날짜 일간 사용"
    hour_boundary: str = "01:30부터 2시간 간격; 23:30부터 자시"
    limitations: list[str] = [
        "역사적 표준시/DST/출생지별 진태양시 보정 미지원",
        "tb_manse를 기존 manse 필드에 대응함; ASP 실 실행 결과 동일성 미검증",
        "원본과 해시를 보존하고 검증된 윤달 표시 교정표 10행을 조회 시 적용함",
        "교정표 적용 후에도 남는 중복 음력키는 임의 선택하지 않음",
        "원본 함수별 야자시 규칙 적용; 원본 미확보 대운 판정은 생성하지 않음",
    ]


class SajuResult(Model):
    solar_birth: str
    lunar_birth: dict
    pillars: dict[str, Pillar]
    day_master: str
    elements: dict[str, int]
    legacy_memno: str
    solar_term_window: dict
    major_luck: dict
    policy: CalendarPolicy = Field(default_factory=CalendarPolicy)


class Score(Model):
    key: str
    label: str
    raw: int
    direction: Literal["opportunity", "caution"]
    favorable: int


class Evidence(Model):
    id: str
    topic: str
    facts: dict
    source: str


class NarrativeTarget(Model):
    id: str
    topic: str
    output_field: str
    evidence_ids: list[str]
    constraints: list[str] = Field(default_factory=list)


class Analysis(Model):
    kind: FortuneKind
    target_date: date
    period_start: date
    period_end: date
    saju: SajuResult
    partner_saju: SajuResult | None = None
    scores: list[Score] = Field(default_factory=list)
    evidence: list[Evidence]
    method: str
    notes: list[str] = Field(default_factory=list)
    source_file: str = ""
    selectors: list[dict] = Field(default_factory=list)
    narrative_contract: list[NarrativeTarget] = Field(default_factory=list)
    unresolved_dependencies: list[str] = Field(default_factory=list)
    ready_for_ai: bool = True


class InterpretationSection(Model):
    target_id: str
    topic: str
    text: str
    evidence_ids: list[str]


class Interpretation(Model):
    summary: str
    sections: list[InterpretationSection]
    practical_advice: list[str]

    def render_text(self) -> str:
        """Present the validated interpretation without creating additional claims."""
        paragraphs = [self.summary]
        paragraphs.extend(f"{section.topic}\n{section.text}" for section in self.sections)
        paragraphs.append("실천 조언\n" + "\n".join(f"- {item}" for item in self.practical_advice))
        return "\n\n".join(paragraphs)


class FortuneResponse(Model):
    content: str | None = Field(
        default=None,
        title="AI un 본문",
        description="실제 AI un 본문(요약·항목별 해석·조언)입니다. 계산전용 요청이면 null입니다.",
    )
    analysis: Analysis
    interpretation: Interpretation | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
