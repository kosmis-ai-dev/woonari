"""CR-021 / T-041: consumer-facing calculation and fortune responses."""

from datetime import date

from pydantic import Field, JsonValue

from app.models import Model, Pillar, Score


class LunarBirthResult(Model):
    year: int
    month: int
    day: int
    leap_month: bool


class PublicSajuResult(Model):
    solar_birth: str
    lunar_birth: LunarBirthResult
    pillars: dict[str, Pillar]
    day_master: str
    elements: dict[str, int]
    solar_term_window: dict[str, JsonValue]


class PublicInterpretationSection(Model):
    topic: str
    text: str


class PublicInterpretation(Model):
    summary: str
    sections: list[PublicInterpretationSection]
    practical_advice: list[str]


class CalculationResult(Model):
    topic: str
    values: dict[str, JsonValue]


class FortuneResult(Model):
    kind: str
    title: str | None = None
    service_id: str | None = None
    target_date: date
    period_start: date
    period_end: date
    saju: PublicSajuResult | None = None
    partner_saju: PublicSajuResult | None = None
    scores: list[Score] = Field(default_factory=list)
    calculations: list[CalculationResult] = Field(default_factory=list)


class PublicFortuneResponse(Model):
    content: str | None = Field(default=None, description="생성된 un 본문입니다. 계산만 요청하면 null입니다.")
    interpretation: PublicInterpretation | None = None
    result: FortuneResult
