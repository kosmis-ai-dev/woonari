"""CR-012: inputs and results for individually ported commercial services."""

from datetime import date

from pydantic import Field, JsonValue, model_validator

from app.models import Birth, Evidence, Interpretation, Model, NarrativeTarget, SajuResult, Score


class ServiceRequest(Model):
    birth: Birth | None = Field(default=None, description="해당 서비스에 생년월일이 필요할 때 입력합니다.")
    partner: Birth | None = Field(default=None, description="두 사람을 비교하는 서비스의 상대방 입력입니다.")
    target_date: date = Field(description="조회 기준 양력 날짜입니다. 별도 server_date 입력이 있는 서비스는 개별 설명을 따릅니다.")
    parameters: dict[str, JsonValue] = Field(
        default_factory=dict,
        description="각 서비스의 한글 설명·예시에 있는 추가 입력만 사용합니다. 원본 판정 코드가 아닌 임의 지시를 넣지 마세요.",
    )
    include_ai: bool = Field(default=True, description="true는 실제 AI 본문, false는 계산·필요자료 진단만 반환합니다.")

    @model_validator(mode="after")
    def validate_period(self):
        if not date(1900, 1, 1) <= self.target_date <= date(2050, 12, 31):
            raise ValueError("target_date 지원 범위는 1900-01-01 ~ 2050-12-31입니다.")
        return self


class ServiceAnalysis(Model):
    service_id: str
    kind: str
    title: str
    target_date: date
    period_start: date
    period_end: date
    saju: SajuResult | None = None
    partner_saju: SajuResult | None = None
    scores: list[Score] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    method: str = "asp-source-python-port"
    notes: list[str] = Field(default_factory=list)
    source_file: str = ""
    selectors: list[dict] = Field(default_factory=list)
    narrative_contract: list[NarrativeTarget] = Field(default_factory=list)
    unresolved_dependencies: list[str] = Field(default_factory=list)
    ready_for_ai: bool = False
    calculation_only: bool = False


class ServiceResponse(Model):
    content: str | None = Field(default=None, description="검증된 실제 AI un 본문입니다. 계산·진단만 실행하면 null입니다.")
    analysis: ServiceAnalysis
    interpretation: Interpretation | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
