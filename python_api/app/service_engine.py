"""CR-012: run only translated source rules; never infer missing DLL/DB decisions."""

from copy import deepcopy
from functools import lru_cache
from importlib import import_module

from app.calendar import calculate_saju, solar_birth
from app.errors import DomainError
from app.fortunes import analyze
from app.legacy_catalog import services
from app.models import Evidence, FortuneKind, FortuneRequest, NarrativeTarget
from app.service_models import ServiceAnalysis, ServiceRequest
from app.source_archive import is_source_archive_configured, resolve_decision
from app.source_catalog import service_archive_status

MODULES = (
    "app.ported_direct", "app.ported_loveunse", "app.ported_remaining", "app.ported_interlife",
    "app.ported_template",
    "app.ported_interlife_extra",
    "app.ported_interlife_dependencies",
    "app.ported_interlife_chart",
    "app.ported_data_rules",
    "app.ported_interlife_leaves",
)


@lru_cache(maxsize=1)
def handlers() -> dict:
    result = {}
    for name in MODULES:
        module = import_module(name)
        for service_id, metadata in module.SERVICES.items():
            if service_id in result:
                raise RuntimeError("Duplicate Python service registration.")
            result[service_id] = (module, metadata)
    return result


@lru_cache(maxsize=1)
def _catalog() -> dict:
    return {item["id"]: item for item in services()}


def service_metadata(service_id: str) -> dict:
    item = _catalog().get(service_id)
    if item is None:
        raise DomainError("unknown_service", "등록되지 않은 un 서비스입니다.", 404)
    entry = deepcopy(item)
    entry["source_archive"] = service_archive_status(entry)
    registered = handlers().get(service_id)
    entry["python_implemented"] = bool(registered or item.get("api_kind"))
    entry["python_module"] = (
        registered[0].__name__ if registered else "app.fortunes" if item.get("api_kind") else None
    )
    entry["python_test_path"] = f"/v1/un/{service_id}"
    entry["python_parameters"] = {
        key: deepcopy(value) for key, value in (registered[1] if registered else {}).items()
        if not key.startswith("_")
    }
    if registered:
        source_classification = {
            "flowerluck": ("TB_FlowerLuck", 366),
            "jewelryluck": ("TB_birthStoneLuck", 12),
        }.get(service_id)
        source_classification_ready = (
            source_classification is not None and is_source_archive_configured()
            and any((t.get("source_table"), t.get("row_count")) == source_classification
                    and t.get("lookup_mapping") == "verified"
                    for t in entry["source_archive"]["tables"])
        )
        ready = registered[1].get("ready", True) or source_classification_ready
        if source_classification_ready and service_id == "jewelryluck":
            entry["python_parameters"]["source_limits"] = [
                "양력 입력은 복원한 월별 보석 자료로 실행합니다. 원본 음력 분기의 미할당 변수 문제로 음력 AI 요청은 자료 진단만 가능합니다.",
            ]
        entry["status"] = "ready" if ready else "source_required"
        entry["status_label"] = (
            "Python 계산·선택키 전환 완료" if ready else "Python 부분 계산 · 원본 판정 자료 필요"
        )
        if ready and registered[1].get("calculation_only"):
            entry["status"] = "calculation_only"
            entry["status_label"] = "Python 계산 전용 전환 완료 · AI 해석 대상 아님"
        elif registered[1].get("calculation_only"):
            entry["status_label"] = "Python 부분 계산 · 원본 행 필요 · AI 해석 대상 아님"
    elif item["status"] == "not_ported":
        entry["status_label"] = "원본·판정 자료 또는 추가 프로필 검증 필요"
    return entry


def service_catalog() -> list[dict]:
    return [service_metadata(service_id) for service_id in _catalog()]


def _births(request: ServiceRequest, metadata: dict, module=None, service_id=""):
    if metadata.get("requires_birth") and request.birth is None:
        raise DomainError("missing_birth", "이 서비스에는 birth 생년월일시 입력이 필요합니다.")
    if metadata.get("requires_partner") and request.partner is None:
        raise DomainError("missing_partner", "이 서비스에는 partner 상대방 입력이 필요합니다.")
    source_dates = getattr(module, "source_birth_dates", None)
    if source_dates:
        dates = source_dates(service_id, request)
    else:
        dates = [solar_birth(birth).date() for birth in (request.birth, request.partner) if birth is not None]
    for birthday in dates:
        if birthday > request.target_date:
            raise DomainError("target_before_birth", "조회 날짜는 출생일 이후여야 합니다.")
    profile = metadata.get("calculation_profile", "dotong")
    saju = calculate_saju(request.birth, profile) if metadata.get("uses_saju") and request.birth else None
    partner = (
        calculate_saju(request.partner, profile)
        if metadata.get("uses_saju") and request.partner else None
    )
    return saju, partner


def _existing(item: dict, request: ServiceRequest) -> ServiceAnalysis:
    if request.birth is None:
        raise DomainError("missing_birth", "이 서비스에는 birth 생년월일시 입력이 필요합니다.")
    parameters = dict(request.parameters)
    if parameters:
        raise DomainError("invalid_service_parameters", "이 기존 서비스에는 해당 추가 입력을 사용할 수 없습니다.")
    try:
        legacy = FortuneRequest(
            birth=request.birth, partner=request.partner, target_date=request.target_date,
            include_ai=request.include_ai,
        )
    except ValueError:
        raise DomainError("invalid_service_parameters", "추가 입력의 형식·허용 범위를 확인하세요.") from None
    result = analyze(FortuneKind(item["api_kind"]), legacy)
    return ServiceAnalysis(
        **result.model_dump(), service_id=item["id"],
        title="연간 un · 사주 기반 AI 해석" if item.get("api_kind") == "yearly" else item["original_name"],
    )


def analyze_service(service_id: str, request: ServiceRequest) -> ServiceAnalysis:
    item = _catalog().get(service_id)
    if item is None:
        raise DomainError("unknown_service", "등록되지 않은 un 서비스입니다.", 404)
    if item.get("api_kind"):
        return _existing(item, request)
    registered = handlers().get(service_id)
    source = next((p for p in item["entrypoints"] if p.endswith(".asp")), "")
    if not registered:
        unresolved = [
            f"{issue['code']}: {issue['reason']}"
            for issue in item["issues"] if issue["code"] != "python_not_ported"
        ] or ["이 항목은 결과 계산 코드가 없는 묶음·참조 항목입니다."]
        return ServiceAnalysis(
            service_id=service_id, kind=service_id, title=item["original_name"],
            target_date=request.target_date, period_start=request.target_date,
            period_end=request.target_date, source_file=source,
            notes=["원본에 없는 판정·분류·점수를 AI가 대신 만들지 않습니다."],
            unresolved_dependencies=unresolved,
        )
    module, metadata = registered
    saju, partner = _births(request, metadata, module, service_id)
    try:
        decision = module.decide(service_id, request, saju, partner)
        decision = resolve_decision(service_id, decision)
    except DomainError:
        raise
    except (KeyError, IndexError, TypeError, ValueError):
        raise DomainError(
            "legacy_rule_unavailable", "원본 분기에 필요한 입력 또는 판정 자료를 확인할 수 없습니다.", 503
        ) from None
    facts = decision.get("facts", {})
    source = decision.get("source", source)
    evidence = [Evidence(id="service-decision", topic="legacy_decision", facts=facts, source=source)]
    if saju:
        evidence.append(Evidence(
            id="natal", topic="natal", source="tb_manse + ASP dotong profile",
            facts={"pillars": {name: value.model_dump() for name, value in saju.pillars.items()}},
        ))
    unresolved = decision.get("unresolved", [])
    selectors = decision.get("selectors", [])
    targets = []
    for index, selector in enumerate(selectors):
        identifier = selector.get("id", f"selection-{index + 1}")
        evidence_id = f"lookup-{identifier}"
        evidence.append(Evidence(
            id=evidence_id, topic="legacy_text_selector", facts=selector, source=source,
        ))
        if unresolved or selector.get("role") == "calculation" or selector.get("narrative") is False:
            continue
        for column in selector.get("columns", []):
            targets.append(NarrativeTarget(
                id=f"{identifier}.{column}",
                topic=selector.get("topics", {}).get(column, selector.get("purpose", item["original_name"])),
                output_field=column, evidence_ids=["service-decision", evidence_id],
                constraints=[
                    "원본 선택키·분기·수치를 유지하고 미확보 사실 속성을 만들지 않는다.",
                    "검증된 source_anchors가 있으면 해당 항목의 표준 원문만 전통적 상징 풀이로 문장화한다. 실제 전생·수명·질병·미래 사건을 확인한 사실로 단정하지 않는다.",
                ],
            ))
    calculation_only = decision.get("calculation_only", metadata.get("calculation_only", False))
    if not unresolved and not targets and not calculation_only:
        unresolved = ["이 분기의 원본 해석 출력 계약이 확정되지 않았습니다."]
    return ServiceAnalysis(
        service_id=service_id, kind=service_id, title=item["original_name"],
        target_date=request.target_date,
        period_start=decision.get("period_start", request.target_date),
        period_end=decision.get("period_end", request.target_date),
        saju=saju, partner_saju=partner, evidence=evidence,
        source_file=source, selectors=selectors, narrative_contract=targets,
        notes=decision.get("notes", []), unresolved_dependencies=unresolved,
        ready_for_ai=not unresolved and bool(targets), calculation_only=calculation_only,
    )
