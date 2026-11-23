"""T-004: transport only; calculation and generation are separately testable."""

import secrets
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path as FilePath
from typing import Annotated

from fastapi import APIRouter, Body, Depends, FastAPI, Header, Path, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.ai import Interpreter, OpenAIInterpreter, validate_interpretation
from app.ai_quota import DailyAIQuota
from app.calendar import calculate_saju
from app.config import Settings, get_settings
from app.errors import DomainError
from app.fortunes import analyze, catalog
from app.legacy_catalog import (
    CATALOG_TAGS,
    LegacyCatalog,
    LegacyService,
    diagnostic_description,
    full_catalog,
    services,
)
from app.manse_store import get_manse_store
from app.models import FortuneKind, FortuneRequest, FortuneResponse, SajuRequest, SajuResult
from app.restored_fortune import restored_data_status
from app.service_engine import analyze_service, service_catalog, service_metadata
from app.service_models import ServiceRequest, ServiceResponse
from app.source_archive import archive_status
from app.swagger_guide import (
    DESCRIPTION,
    ERROR_RESPONSES,
    READY_TAG,
    SAJU_EXAMPLES,
    TAGS,
    WAITING_KINDS,
    WAITING_TAG,
    fortune_description,
    fortune_examples,
    generic_examples,
)


def get_interpreter(request: Request) -> Interpreter:
    return request.app.state.interpreter


def authorize(
    request: Request,
    x_api_key: Annotated[
        str | None,
        Header(description="API_KEY 설정 시에만 입력합니다. 로컬 기본 설정에서는 비워두세요."),
    ] = None,
):
    expected = request.app.state.settings.api_key
    if expected and expected.get_secret_value():
        if not x_api_key or not secrets.compare_digest(
            x_api_key.encode(), expected.get_secret_value().encode()
        ):
            raise DomainError("unauthorized", "유효한 X-API-Key가 필요합니다.", 401)


def _default_interpreter(settings: Settings) -> Interpreter:
    if settings.ai_provider == "bedrock":
        from app.bedrock import BedrockInterpreter

        return BedrockInterpreter(settings)
    return OpenAIInterpreter(settings)


def create_app(
    settings: Settings | None = None,
    *,
    interpreter_factory: Callable[[Settings], Interpreter] | None = None,
    ai_quota: DailyAIQuota | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        factory = interpreter_factory or _default_interpreter
        application.state.interpreter = factory(application.state.settings)
        # Both production providers share one ledger across routes and aliases.
        if hasattr(application.state.interpreter, "reserve_call"):
            application.state.interpreter.reserve_call = application.state.ai_quota.reserve
        try:
            yield
        finally:
            await application.state.interpreter.close()

    application = FastAPI(
        title="un API",
        version="0.1.0",
        lifespan=lifespan,
        description=DESCRIPTION,
        openapi_tags=[*TAGS,
            {"name": "Python 추가 전환 · 계산 가능", "description": "원본에서 옮긴 추가 계산·문구 선택 규칙을 실행합니다."},
            {"name": "Python 추가 전환 · 자료 진단", "description": "부분 계산과 필요한 원본 자료를 확인합니다. 진단 성공은 최종 un 생성 성공을 뜻하지 않습니다."},
        ],
        swagger_ui_parameters={
            "docExpansion": "list",
            "defaultModelsExpandDepth": 0,
            "filter": True,
            "displayRequestDuration": True,
        },
    )
    application.state.settings = settings or get_settings()
    state_root = FilePath(__file__).resolve().parents[2] / ".local/woonari"
    application.state.ai_quota = ai_quota or DailyAIQuota(
        state_root / "ai/usage.sqlite3", private_root=state_root,
        limit=application.state.settings.ai_daily_call_limit,
    )

    @application.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        return JSONResponse(
            status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}}
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Do not echo supplied birth data, input text or credentials into error responses.
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_request",
                    "message": "입력값을 확인해 주세요.",
                    "fields": [
                        {"location": list(e["loc"]), "message": e["msg"], "type": e["type"]}
                        for e in exc.errors()
                    ],
                }
            },
        )

    @application.get(
        "/health", tags=["서버 상태"], summary="서버 상태 확인",
        description="AI 설정 여부를 확인합니다. ai_configured는 선택한 제공자의 필수 설정 유무이며, 실제 모델 호출·AWS 권한 검증 완료 여부는 아닙니다.",
    )
    def health():
        configuration = application.state.settings
        missing_settings = []
        if configuration.ai_provider == "bedrock":
            if not configuration.bedrock_model_id.strip():
                missing_settings.append("BEDROCK_MODEL_ID")
            if not configuration.bedrock_region.strip():
                missing_settings.append("BEDROCK_REGION")
            if configuration.bedrock_auth_mode == "api_key" and not configuration.bedrock_account_id:
                missing_settings.append("BEDROCK_ACCOUNT_ID")
        else:
            if not (
                configuration.openai_api_key
                and configuration.openai_api_key.get_secret_value().strip()
            ):
                missing_settings.append("OPENAI_API_KEY")
            if not configuration.openai_model.strip():
                missing_settings.append("OPENAI_MODEL")
        return {
            "status": "ok", "calendar_policy": "asp-manse-db-v4",
            "lunar_correction_version": "lunar-leap-flags-v1",
            "calendar_backend": get_manse_store().backend,
            "ai_provider": configuration.ai_provider,
            "bedrock_auth_mode": configuration.bedrock_auth_mode if configuration.ai_provider == "bedrock" else None,
            "ai_daily_call_limit": application.state.ai_quota.limit,
            "ai_configured": not missing_settings,
            "ai_missing_settings": missing_settings,
        }

    router = APIRouter(prefix="/v1", dependencies=[Depends(authorize)])

    @router.get(
        "/ai-usage", tags=["시작 안내"], summary="AI 일일 사용량 · 한국시간 최대 100회",
        description="Woonari의 AI 호출 시도 사용량입니다. 한국시간 매일 00:00 기준이며 실제 전송 이후 오류도 차감합니다. 계산·자료 진단은 차감하지 않습니다.",
    )
    def ai_usage():
        return application.state.ai_quota.status()

    @router.get(
        "/restored-data", tags=["시작 안내"], summary="복원 DB · 연간 un 자료와 남은 문제 확인",
        description="백업에서 선별한 연간 7,000행·월별 1,200행의 MySQL 적재 상태를 조회합니다. "
        "2021~2050년은 빈 본문·기본 점수인 초기 행입니다. 2027년 140행의 존재는 완성된 판정을 뜻하지 않습니다. "
        "원본 키·성별·항목 매핑도 확인이 필요합니다. AI 호출 없이 문제를 확인하며 회원·결제·본문은 반환하지 않습니다.",
    )
    def restored_data(year: Annotated[int, Query(ge=2001, le=2050)] = 2027):
        return restored_data_status(year)

    @router.get(
        "/source-data", tags=["시작 안내"], summary="회원 제외 · un 전체 복원 자료와 연결 상태",
        description="비회원 un 정의·판정·사전 자료의 원본 출처와 실제 MySQL 행 수를 확인합니다. "
        "복원됨·빈 원본·조회 규칙 미확정을 구분하며, 표가 있다는 이유로 모든 un이 완성됐다고 판정하지 않습니다. "
        "회원·상담·결제·연락처·로그 및 원문은 반환하지 않고 AI도 호출하지 않습니다.",
    )
    def source_data():
        return archive_status()

    @router.get(
        "/fortunes", tags=["시작 안내"], summary="현재 Python 10종 · un 한글 목록과 테스트 상태",
        description="현재 계산/조회키 경로가 구현된 10종입니다. **ASP 전체 항목은 GET /v1/asp-services**와 아래 ASP 전체 태그에서 확인하세요.",
    )
    def fortunes():
        return {"items": catalog()}

    @router.get("/un-services", tags=["시작 안내"], summary="Python 전체 서비스 · 실행 경로와 추가 입력")
    def python_services():
        items = service_catalog()
        return {"count": len(items), "items": items}

    async def run_service(service_id: str, body: ServiceRequest, interpreter: Interpreter):
        result = await run_in_threadpool(analyze_service, service_id, body)
        if not body.include_ai:
            return ServiceResponse(analysis=result)
        if result.calculation_only:
            raise DomainError("ai_not_applicable", "이 서비스는 계산 전용입니다. include_ai=false로 실행하세요.")
        if not result.ready_for_ai:
            raise DomainError(
                "legacy_dependency_unavailable",
                "원본 판정 자료 또는 출력 계약이 필요합니다. include_ai=false로 unresolved_dependencies를 확인하세요.",
                503,
            )
        interpretation = validate_interpretation(await interpreter.interpret(result), result)
        return ServiceResponse(
            content=interpretation.render_text(), analysis=result, interpretation=interpretation,
            ai_provider=interpreter.name, ai_model=interpreter.model,
        )

    def make_service_endpoint(service_id: str, samples: dict):
        async def endpoint(
            body: Annotated[ServiceRequest, Body(openapi_examples=samples)],
            interpreter: Annotated[Interpreter, Depends(get_interpreter)],
        ):
            return await run_service(service_id, body, interpreter)

        return endpoint

    for original in services():
        item = service_metadata(original["id"])
        metadata = item["python_parameters"]
        calculation_ready = item["status"] in {"ready", "calculation_only"} and item["python_implemented"]
        calculation_only = bool(metadata.get("calculation_only"))
        ready = calculation_ready and not calculation_only
        sample = {
            "target_date": "2014-11-18" if item.get("api_kind") == "yearly" else "2026-11-18",
            "parameters": metadata.get("example_parameters", {}), "include_ai": ready,
        }
        if metadata.get("requires_birth") or item.get("api_kind"):
            sample["birth"] = {
                "year": 1990, "month": 5, "day": 17, "hour": 14, "minute": 30,
                "gender": "male", "calendar": "solar",
            }
        if metadata.get("requires_partner") or item.get("api_kind") == "compatibility":
            sample["partner"] = {
                "year": 1992, "month": 7, "day": 15, "hour": 12, "minute": 0,
                "gender": "female", "calendar": "solar",
            }
        if item.get("api_kind") == "career":
            sample["parameters"] = {"career_category": "A"}
        samples = {"recommended": {
            "summary": "AI 본문 생성" if ready else "계산 전용 실행" if calculation_only and calculation_ready else "계산·자료 진단만 확인",
            "value": sample,
        }}
        if ready:
            samples["calculation_only"] = {
                "summary": "계산만 확인 · AI 호출 없음", "value": {**sample, "include_ai": False},
            }
        descriptions = [
            f"**{item['name']}** · {item['status_label']}",
            "Try it out → Examples → Execute로 실행합니다. content는 실제 AI 본문, analysis는 계산 근거입니다.",
            "비회원 자료의 전체 복원 상태는 GET /v1/source-data, 이 항목의 표별 상태는 GET /v1/un-services 응답의 source_archive에서 확인합니다.",
        ]
        parameter_help = metadata.get("parameter_help", {})
        if isinstance(parameter_help, dict):
            descriptions.extend(
                f"- `parameters.{key}`: {description}" for key, description in parameter_help.items()
            )
        elif isinstance(parameter_help, str):
            descriptions.append(parameter_help)
        limits = metadata.get("source_limits", [])
        limits = [limits] if isinstance(limits, str) else limits
        descriptions.extend(f"- 원본 제약: {value}" for value in limits)
        if calculation_only:
            descriptions.append("원본이 날짜·그래프 등 계산 결과만 출력하는 서비스이므로 AI 해석을 요청하지 않습니다.")
        if item["status"] == "source_required":
            descriptions.append("원본에 없는 계산을 AI로 대체하지 않습니다. unresolved_dependencies를 확인하세요.")
        router.add_api_route(
            f"/un/{item['id']}", make_service_endpoint(item["id"], samples), methods=["POST"],
            response_model=ServiceResponse, summary=f"{item['name']} · {'계산·해석' if ready else '계산 전용' if calculation_only and calculation_ready else '원본 자료 진단'}",
            description="\n\n".join(descriptions),
            tags=["Python 추가 전환 · 계산 가능" if calculation_ready else "Python 추가 전환 · 자료 진단"],
            operation_id=f"run_python_un_{item['id'].replace('-', '_')}", responses=ERROR_RESPONSES,
        )

    @router.post(
        "/un/{service_id}", response_model=ServiceResponse, include_in_schema=False,
    )
    async def python_un(
        service_id: str, body: ServiceRequest,
        interpreter: Annotated[Interpreter, Depends(get_interpreter)],
    ):
        return await run_service(service_id, body, interpreter)

    @router.get(
        "/asp-services",
        response_model=LegacyCatalog,
        tags=["시작 안내"],
        summary="ASP 전체 목록 · 실제 이름·문제 원인·해결 자료",
        description="보관 원본에서 조사한 전체 목록입니다. **Try it out → Execute**로 조회합니다. `issues`의 `reason`, `resolution`, `required_materials`, `sources`에서 원인과 해결 자료를 확인하세요. **GET 200은 목록 조회 성공입니다.** Python 실행 경로와 추가 입력은 GET /v1/un-services 및 POST /v1/un/{id}에서 확인합니다.",
        responses={401: ERROR_RESPONSES[401]},
    )
    def asp_services():
        configuration = application.state.settings
        if configuration.ai_provider == "bedrock":
            return full_catalog(
                ai_key_configured=None,
                ai_model_configured=bool(configuration.bedrock_model_id.strip()),
                ai_region_configured=bool(configuration.bedrock_region.strip()),
                ai_provider="bedrock",
                ai_auth_mode=configuration.bedrock_auth_mode,
                ai_account_configured=bool(configuration.bedrock_account_id),
            )
        return full_catalog(
            ai_key_configured=bool(
                configuration.openai_api_key
                and configuration.openai_api_key.get_secret_value().strip()
            ),
            ai_model_configured=bool(configuration.openai_model.strip()),
        )

    def make_diagnostic_endpoint(item: dict):
        def endpoint():
            return item

        return endpoint

    for item in services():
        router.add_api_route(
            item["diagnostic_path"].removeprefix("/v1"),
            make_diagnostic_endpoint(item),
            methods=["GET"],
            response_model=LegacyService,
            summary=f"{item['name']} · {item['status_label'].split(' · ')[0]}",
            description=diagnostic_description(item),
            tags=[CATALOG_TAGS[item["status"]]],
            operation_id=f"inspect_asp_{item['id'].replace('-', '_')}",
            responses={
                200: {
                    "description": "상태·문제 조회 성공. 계산 실행 결과가 아닙니다.",
                    "content": {"application/json": {"example": item}},
                },
                401: ERROR_RESPONSES[401],
            },
        )

    @router.post(
        "/saju",
        response_model=SajuResult,
        tags=["사주 계산"],
        summary="사주팔자 계산 · 양력/음력 변환",
        responses={code: ERROR_RESPONSES[code] for code in (401, 422, 503)},
        description="un 생성 전에 사주팔자를 확인합니다. **Try it out → Examples → Execute**로 실행하세요. AI 키가 필요하지 않습니다. 결과의 `pillars`에서 `hangul`을 보면 한글 간지를 확인할 수 있습니다.",
    )
    def saju(body: Annotated[SajuRequest, Body(openapi_examples=SAJU_EXAMPLES)]):
        return calculate_saju(body.birth, profile=body.calculation_profile)

    async def run_fortune(
        kind: FortuneKind,
        body: FortuneRequest,
        interpreter: Annotated[Interpreter, Depends(get_interpreter)],
    ):
        result = await run_in_threadpool(analyze, kind, body)
        if not body.include_ai:
            return FortuneResponse(analysis=result)
        if not result.ready_for_ai:
            raise DomainError(
                "legacy_dependency_unavailable",
                "원본 판정 의존성이 필요합니다. include_ai=false로 선택키와 unresolved_dependencies를 확인하세요.",
                503,
            )
        interpretation = validate_interpretation(await interpreter.interpret(result), result)
        return FortuneResponse(
            content=interpretation.render_text(),
            analysis=result,
            interpretation=interpretation,
            ai_provider=interpreter.name,
            ai_model=interpreter.model,
        )

    def make_fortune_endpoint(kind: FortuneKind):
        async def endpoint(
            body: Annotated[FortuneRequest, Body(openapi_examples=fortune_examples(kind))],
            interpreter: Annotated[Interpreter, Depends(get_interpreter)],
        ):
            return await run_fortune(kind, body, interpreter)

        return endpoint

    # Register concrete routes before the parameterized compatibility route.
    for item in catalog():
        kind = FortuneKind(item["id"])
        waiting = kind in WAITING_KINDS
        router.add_api_route(
            f"/fortunes/{kind.value}",
            make_fortune_endpoint(kind),
            methods=["POST"],
            response_model=FortuneResponse,
            summary=f"{item['name']} · {'조회키 진단 전용' if waiting else '계산·해석 테스트'}",
            description=fortune_description(kind),
            tags=[WAITING_TAG if waiting else READY_TAG],
            operation_id=f"test_fortune_{kind.value}",
            responses=ERROR_RESPONSES,
        )

    @router.post(
        "/fortunes/{kind}",
        response_model=FortuneResponse,
        tags=["공통 호출"],
        summary="공통 un 호출 · kind로 un 선택",
        responses=ERROR_RESPONSES,
        description="기존 통합 경로입니다. 처음에는 위의 한글 un별 테스트 항목을 사용하세요. Examples를 바꾼 후 **kind도 해당 코드로 직접 선택**해야 합니다.\n\n"
        + " / ".join(f"{x['id']}={x['name']}" for x in catalog()),
    )
    async def fortune(
        kind: Annotated[
            FortuneKind,
            Path(
                title="un 종류",
                description="un 코드입니다. 한글 이름은 위 설명과 개별 테스트 항목을 참고하세요.",
            ),
        ],
        body: Annotated[FortuneRequest, Body(openapi_examples=generic_examples())],
        interpreter: Annotated[Interpreter, Depends(get_interpreter)],
    ):
        return await run_fortune(kind, body, interpreter)

    application.include_router(router)
    return application


app = create_app()
