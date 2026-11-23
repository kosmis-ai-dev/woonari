"""CR-004 / T-011: audited ASP services, separate from executable fortune kinds.

The checked-in catalog contains source references only. Serving it never executes
ASP/COM/SQL and never reads legacy connection strings.
"""

import json
from collections import Counter
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.restored_fortune import BACKUP_FINDING
from app.source_archive import is_source_archive_configured
from app.source_catalog import service_archive_status


class SourceReference(BaseModel):
    path: str = Field(description="보관된 원본 파일의 저장소 상대 경로")
    line: int = Field(ge=1, description="이름·호출·조회 등을 확인한 원본 줄 번호")
    detail: str = Field(description="이 위치에서 확인한 사실")


class LegacyIssue(BaseModel):
    code: str = Field(description="문제 추적 코드")
    certainty: Literal["confirmed", "needs_review"] = Field(
        description="confirmed=소스/현재 구현으로 확인, needs_review=추가 검증 필요"
    )
    reason: str = Field(description="왜 현재 실행할 수 없거나 검증이 필요한지")
    effect: str = Field(description="계산·판정·AI 해석에 미치는 영향")
    resolution: list[str] = Field(description="해결할 작업의 구체적인 순서")
    required_materials: list[str] = Field(description="확인 또는 제공이 필요한 자료. 없으면 빈 배열")
    sources: list[SourceReference] = Field(default_factory=list, description="원인 판단의 원본 근거")


class LegacyService(BaseModel):
    id: str = Field(description="전체 ASP 목록용 식별자. 계산 API의 kind와 별개입니다.")
    name: str = Field(description="Swagger 표시명 (운세 문구는 un으로 표시)")
    original_name: str = Field(description="원본 메뉴·결과 코드에서 확인한 실제 한글 이름")
    aliases: list[str] = Field(default_factory=list, description="다른 메뉴명·구분명")
    menu_codes: list[str] = Field(default_factory=list, description="원본 XML 메뉴 코드 (IM번호)")
    classification: Literal["service", "archive", "container", "utility"] = Field(
        description="service=개별 서비스, archive=과거판, container=하위 서비스 묶음, utility=보조 코드"
    )
    category: str = Field(description="원본 서비스 분류")
    directory: str = Field(description="원본 디렉터리")
    entrypoints: list[str] = Field(description="결과/입력 ASP 파일 또는 코드별 분기 진입점")
    parameters: dict = Field(default_factory=dict, description="같은 ASP 안에서 하위 서비스를 선택하는 원본 요청값")
    parent_id: str | None = Field(default=None, description="묶음의 상위 식별자")
    children: list[str] = Field(default_factory=list, description="하위 서비스 식별자")
    related_service_ids: list[str] = Field(default_factory=list, description="이름이 겹치는 다른 원본. 로직 동일성을 뜻하지 않습니다.")
    status: Literal["ready", "calculation_only", "source_required", "not_ported", "archived", "reference"]
    status_label: str = Field(description="현재 Python에서 가능한 범위")
    api_kind: str | None = Field(default=None, description="기존 계산 API가 있을 때만 해당 kind")
    test_path: str | None = Field(default=None, description="현재 실행 가능한 POST 계산 경로")
    diagnostic_path: str = Field(description="이 항목의 상태·문제 조회 GET 경로")
    issues: list[LegacyIssue] = Field(description="현재 문제와 해결 방법. 정상 항목은 빈 배열")
    dependencies: list[dict] = Field(default_factory=list, description="확인된 데이터/파일 의존성과 판정 필드. 실제 DB 접속 가능 여부는 별도 검증 대상")
    sources: list[SourceReference] = Field(description="실제 이름과 로직을 확인한 근거")
    review_notes: list[str] = Field(default_factory=list, description="정적 조사 범위와 검증 한계")
    source_archive: dict = Field(default_factory=dict, description="회원 제외 복원 자료·원본 조회 대응 상태. 현재 연결 검증은 /v1/source-data에서 확인")


class LegacyCatalog(BaseModel):
    summary: dict = Field(description="디렉터리/실제 서비스/상태별 수량과 조사 범위")
    common_notes: list[str] = Field(description="제공 만세력 DB·AI 연결 등 모든 항목의 공통 조건")
    ai_configuration: dict = Field(description="선택한 AI 제공자의 인증 방식과 모델·리전 설정 여부. 비밀값과 실제 모델명은 반환하지 않습니다.")
    menu_map: list[dict] = Field(description="원본 IM1~IM90 메뉴와 목록 항목 매핑. 누락된 연결도 포함합니다.")
    items: list[LegacyService]


STATUS_LABELS = {
    "ready": "계산·선택키 이식 완료 · AI 연결 설정 필요",
    "calculation_only": "Python 계산 전용 전환 완료 · AI 해석 대상 아님",
    "source_required": "원본·판정 자료 또는 계산 프로필 검증 필요",
    "not_ported": "Python 미이식 · 원본 로직 분석/이식 필요",
    "archived": "과거 연도판 · 개별 이식/대상 연도 검토 필요",
    "reference": "묶음 또는 보조 코드 · 개별 계산 대상 아님",
}
CATALOG_TAGS = {
    "ready": "ASP 전체 · 이식 완료",
    "calculation_only": "ASP 전체 · 계산 전용",
    "source_required": "ASP 전체 · 원본 판정 자료 필요",
    "not_ported": "ASP 전체 · 추가 이식 대상",
    "archived": "ASP 전체 · 과거 연도판",
    "reference": "ASP 전체 · 묶음·보조 코드",
}


@lru_cache(maxsize=1)
def _catalog_data() -> dict:
    source = Path(__file__).with_name("data") / "legacy_services.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    for item in data["items"]:
        if item.get("api_kind") == "yearly":
            item.setdefault("review_notes", []).append(BACKUP_FINDING)
    # Validate checked-in data on startup/OpenAPI generation, not only in tests.
    data["items"] = [LegacyService.model_validate(item).model_dump() for item in data["items"]]
    return data


def services() -> list[dict]:
    result = deepcopy(_catalog_data()["items"])
    for item in result:
        item["source_archive"] = service_archive_status(item)
        source = {"flowerluck": ("TB_FlowerLuck", 366, "birth_flower_identity_missing"),
                  "jewelryluck": ("TB_birthStoneLuck", 12, "birth_stone_identity_missing")}.get(item["id"])
        if (source and is_source_archive_configured()
                and any(t.get("source_table") == source[0] and t.get("row_count") == source[1]
                        and t.get("lookup_mapping") == "verified"
                        for t in item["source_archive"]["tables"])):
            item["status"] = "ready"
            item["status_label"] = "Python 원본 자료 연결 완료 · 실행 시 행 검증"
            item["test_path"] = f"/v1/un/{item['id']}"
            item["issues"] = [issue for issue in item["issues"] if issue["code"] != source[2]]
            if item["id"] == "jewelryluck":
                item["review_notes"].append("양력 월별 원본 자료를 연결했습니다. 음력 분기의 lmyMonth/lmyDay 미할당 문제는 남아 있어 음력 요청의 AI 생성은 차단합니다.")
    return result


def full_catalog(
    *,
    ai_key_configured: bool | None,
    ai_model_configured: bool,
    ai_provider: Literal["openai", "bedrock"] = "openai",
    ai_region_configured: bool | None = None,
    ai_auth_mode: Literal["iam", "api_key"] = "iam",
    ai_account_configured: bool = False,
) -> dict:
    data = deepcopy(_catalog_data())
    items = data["items"] = services()
    data["summary"].update(
        records=len(items),
        classifications=dict(Counter(item["classification"] for item in items)),
        statuses=dict(Counter(item["status"] for item in items)),
        issues_by_certainty=dict(
            Counter(issue["certainty"] for item in items for issue in item["issues"])
        ),
    )
    bedrock = ai_provider == "bedrock"
    bearer = bedrock and ai_auth_mode == "api_key"
    data["ai_configuration"] = {
        "provider": ai_provider,
        "authentication": "bedrock_api_key" if bearer else "aws_iam" if bedrock else "api_key",
        "key_required": bearer or not bedrock,
        "key_configured": None if bedrock else ai_key_configured,
        "model_configured": ai_model_configured,
        "region_configured": ai_region_configured if bedrock else None,
        "account_configured": ai_account_configured if bearer else None,
        "configuration_complete": bool(
            ai_model_configured and (ai_region_configured if bedrock else ai_key_configured)
            and (ai_account_configured if bearer else True)
        ),
        "generation_check": "not_run",
        "note": "필수 설정의 존재 여부만 확인하며 이 조회는 AI를 호출하지 않습니다. 실제 계정·권한과 응답 검증은 개별 POST에서 include_ai=true로 실행합니다.",
    }
    return data


def diagnostic_description(item: dict) -> str:
    lines = [
        f"**원본 이름:** {item['original_name']}  ",
        f"**분류:** {item['category']} / {item['classification']}  ",
        f"**현재 상태:** {item['status_label']}  ",
        f"**원본 위치:** `{item['directory']}`",
        "",
        "**이 GET은 상태·문제 조회입니다.** Try it out → Execute로 입력 없이 확인합니다.",
    ]
    if item["aliases"]:
        lines.append("다른 이름: " + " / ".join(item["aliases"]))
    lines += ["", "**비회원 un 자료 복원:** `GET /v1/source-data`에서 실제 적재 상태를 확인합니다. "
              "목록 응답의 source_archive는 확보한 표·행 수와 조회 규칙 확인 여부를 구분합니다."]
    if item["menu_codes"]:
        lines.append("원본 메뉴 코드: " + ", ".join(item["menu_codes"]))
    if item["parameters"]:
        lines.append("원본 분기 요청값: " + ", ".join(f"`{key}={value}`" for key, value in item["parameters"].items()))
    for dependency in item["dependencies"]:
        if "calculation" in dependency:
            calculation = dependency["calculation"]
            lines += [f"**원본 계산 함수:** `{calculation['helper']}`", f"**판정 방식:** {calculation['summary']}"]
    if item["children"]:
        lines.append("하위 항목: " + ", ".join(f"`{child}`" for child in item["children"]))
    if item["related_service_ids"]:
        lines.append("이름이 겹치는 별도 원본: " + ", ".join(f"`{related}`" for related in item["related_service_ids"]))
    if item["test_path"]:
        include_ai = "true" if item["status"] == "ready" else "false"
        lines.append(f"계산 요청: **POST `{item['test_path']}`**, 기본 예시 `include_ai={include_ai}`.")
    else:
        lines.append("현재 Python 계산 경로는 없습니다. 이 항목에서 최종 해석은 생성하지 않습니다.")
    for issue in item["issues"]:
        certainty = "확인된 문제" if issue["certainty"] == "confirmed" else "추가 확인 필요"
        lines += [
            "",
            f"### {issue['code']} · {certainty}",
            f"**원인:** {issue['reason']}",
            f"**영향:** {issue['effect']}",
            "**해결:**",
            *[f"{i}. {step}" for i, step in enumerate(issue["resolution"], 1)],
        ]
        if issue["required_materials"]:
            lines += ["**필요 자료:**", *[f"- {material}" for material in issue["required_materials"]]]
    if not item["issues"] and item["status"] == "ready":
        lines.append("현재 이식 범위에서 미해결 판정 의존성은 없습니다. 실제 AI 생성에는 선택한 제공자의 인증·모델 설정이 필요합니다.")
    elif item["status"] == "calculation_only":
        lines.append("원본은 달력·만세력 계산 결과를 제공하는 서비스입니다. include_ai=false로 실행하며 해석 문장을 생성하지 않습니다.")
    elif not item["issues"]:
        lines.append("묶음·보조 코드입니다. 계산 가능 여부는 하위 개별 서비스의 상태를 확인하세요.")
    lines += ["", "### 원본 근거"]
    lines += [f"- `{ref['path']}:{ref['line']}` — {ref['detail']}" for ref in item["sources"]]
    if item["review_notes"]:
        lines += ["", "### 확인 범위", *[f"- {note}" for note in item["review_notes"]]]
    return "\n".join(lines)
