"""T-004: transport only; calculation and generation are separately testable."""

import secrets
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path as FilePath
from typing import Annotated

from fastapi import APIRouter, Body, Depends, FastAPI, Header, Path, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.ai import Interpreter, OpenAIInterpreter, validate_interpretation
from app.ai_quota import DailyAIQuota
from app.calendar import calculate_saju
from app.config import Settings, get_settings
from app.errors import DomainError
from app.fortunes import analyze, catalog
from app.legacy_catalog import services
from app.manse_store import get_manse_store
from app.models import FortuneKind, FortuneRequest, SajuRequest
from app.public_catalog import (
    PublicServiceCatalog,
    available_services,
    calculation_request,
    public_service,
)
from app.public_errors import public_error
from app.public_models import PublicFortuneResponse, PublicSajuResult
from app.public_results import fortune_response, saju_result, service_response
from app.service_engine import analyze_service, service_catalog, service_metadata
from app.service_models import ServiceRequest
from app.service_offerings import (
    SERVICE_TAG,
    service_offering_description,
    service_operation_tag,
)
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
        openapi_tags=TAGS,
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
        status, content = public_error(exc)
        return JSONResponse(status_code=status, content=content)

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
            "status": "ok",
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
        description="Woonari의 AI 호출 시도 사용량입니다. 한국시간 매일 00:00 기준이며 실제 전송 이후 오류도 차감합니다. 계산 요청은 차감하지 않습니다.",
    )
    def ai_usage():
        return application.state.ai_quota.status()

    @router.get(
        "/fortunes", response_model=PublicServiceCatalog, tags=["시작 안내"],
        summary="un 종류와 호출 경로", description="현재 제공하는 기본 un의 이름과 입력 정보를 확인합니다.",
    )
    def fortunes():
        items = [public_service(item, core=True) for item in available_services(service_catalog()) if item.get("api_kind")]
        return PublicServiceCatalog(count=len(items), items=items)

    @router.get(
        "/un-services", response_model=PublicServiceCatalog, tags=["시작 안내"],
        summary="전체 콘텐츠와 입력 안내", description="현재 결과를 제공하는 콘텐츠의 호출 경로와 추가 입력입니다.",
    )
    def python_services():
        items = [public_service(item) for item in available_services(service_catalog())]
        return PublicServiceCatalog(count=len(items), items=items)

    async def run_service(service_id: str, body: ServiceRequest, interpreter: Interpreter):
        result = await run_in_threadpool(analyze_service, service_id, calculation_request(body))
        if result.unresolved_dependencies or not (result.ready_for_ai or result.calculation_only):
            raise DomainError("result_unavailable", "현재 이 요청의 결과를 제공할 수 없습니다.", 503)
        if not body.include_ai:
            return service_response(result)
        if result.calculation_only:
            raise DomainError("ai_not_applicable", "이 서비스는 계산 전용입니다. include_ai=false로 실행하세요.")
        interpretation = validate_interpretation(await interpreter.interpret(result), result)
        return service_response(result, interpretation)

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
        public_item = public_service(item)
        sample = {
            "target_date": "2027-01-01" if item.get("api_kind") == "yearly" else "2026-11-18",
            "parameters": public_item.parameter_examples, "include_ai": ready,
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
        samples = {"recommended": {
            "summary": "AI 본문 생성" if ready else "계산 전용 실행" if calculation_only and calculation_ready else "계산·자료 진단만 확인",
            "value": sample,
        }}
        if ready:
            samples["calculation_only"] = {
                "summary": "계산만 확인 · AI 호출 없음", "value": {**sample, "include_ai": False},
            }
        descriptions = [
            f"**{item['name']}**",
            "Try it out → Examples → Execute로 실행합니다. content는 운세 본문, result는 계산 결과입니다."
        ]
        parameter_help = public_item.parameter_help
        if isinstance(parameter_help, dict):
            descriptions.extend(
                f"- `parameters.{key}`: {description}" for key, description in parameter_help.items()
            )
        elif isinstance(parameter_help, str):
            descriptions.append(parameter_help)
        if calculation_only:
            descriptions.append("계산 결과만 제공합니다. include_ai=false로 실행하세요.")
        path = f"/v1/un/{item['id']}"
        tag = service_operation_tag(
            path, ready=ready, calculation_only=calculation_only and calculation_ready,
        )
        if tag == SERVICE_TAG:
            descriptions.insert(0, service_offering_description(path))
        router.add_api_route(
            f"/un/{item['id']}", make_service_endpoint(item["id"], samples), methods=["POST"],
            response_model=PublicFortuneResponse, include_in_schema=calculation_ready, summary=f"{item['name']} · {'AI 본문 생성' if tag == SERVICE_TAG else '계산·해석' if ready else '계산 전용' if calculation_only and calculation_ready else '현재 미지원'}",
            description="\n\n".join(descriptions),
            tags=[tag],
            operation_id=f"run_python_un_{item['id'].replace('-', '_')}", responses=ERROR_RESPONSES,
        )

    @router.post(
        "/un/{service_id}", response_model=PublicFortuneResponse, include_in_schema=False,
    )
    async def python_un(
        service_id: str, body: ServiceRequest,
        interpreter: Annotated[Interpreter, Depends(get_interpreter)],
    ):
        return await run_service(service_id, body, interpreter)

    @router.post(
        "/saju",
        response_model=PublicSajuResult,
        tags=["사주 계산"],
        summary="사주팔자 계산 · 양력/음력 변환",
        responses={code: ERROR_RESPONSES[code] for code in (401, 422, 503)},
        description="un 생성 전에 사주팔자를 확인합니다. **Try it out → Examples → Execute**로 실행하세요. AI 키가 필요하지 않습니다. 결과의 `pillars`에서 `hangul`을 보면 한글 간지를 확인할 수 있습니다.",
    )
    def saju(body: Annotated[SajuRequest, Body(openapi_examples=SAJU_EXAMPLES)]):
        return saju_result(calculate_saju(body.birth, profile=body.calculation_profile))

    async def run_fortune(
        kind: FortuneKind,
        body: FortuneRequest,
        interpreter: Annotated[Interpreter, Depends(get_interpreter)],
    ):
        result = await run_in_threadpool(analyze, kind, body)
        if not result.ready_for_ai:
            raise DomainError("result_unavailable", "현재 이 요청의 결과를 제공할 수 없습니다.", 503)
        if not body.include_ai:
            return fortune_response(result)
        interpretation = validate_interpretation(await interpreter.interpret(result), result)
        return fortune_response(result, interpretation)

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
            methods=["POST"], include_in_schema=not waiting,
            response_model=PublicFortuneResponse,
            summary=f"{item['name']} · {'조회키 진단 전용' if waiting else 'AI 본문 생성'}",
            description=fortune_description(kind),
            tags=[WAITING_TAG if waiting else READY_TAG],
            operation_id=f"test_fortune_{kind.value}",
            responses=ERROR_RESPONSES,
        )

    @router.post(
        "/fortunes/{kind}",
        response_model=PublicFortuneResponse,
        tags=["공통 호출"],
        summary="공통 un 호출 · kind로 un 선택",
        responses=ERROR_RESPONSES,
        description="기존 통합 경로입니다. 처음에는 위의 한글 un별 테스트 항목을 사용하세요. Examples를 바꾼 후 **kind도 해당 코드로 직접 선택**해야 합니다.\n\n"
        + " / ".join(f"{x['id']}={x['name']}" for x in catalog() if FortuneKind(x["id"]) not in WAITING_KINDS),
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
