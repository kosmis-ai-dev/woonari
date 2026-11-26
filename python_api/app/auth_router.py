"""CR-022 / T-042: browser OAuth and Bearer session endpoints."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth_models import (
    AuthorizationResult,
    AuthUser,
    BirthProfilePatch,
    LoginResult,
    LogoutResult,
    MemberBirthProfile,
    ProviderList,
    RefreshRequest,
    SocialProvider,
)
from app.auth_service import STATE_SECONDS, AuthService, cookie_name
from app.errors import DomainError
from app.models import Birth

TAG = "소셜 로그인 · 카카오·구글·네이버"
MEMBER_BIRTH_TAG = "회원 사주 정보"
_BEARER = HTTPBearer(auto_error=False, description="소셜 로그인에서 받은 access_token을 입력합니다.")
_NAMES = {SocialProvider.kakao: "카카오", SocialProvider.google: "구글", SocialProvider.naver: "네이버"}
_BIRTH_EXAMPLE = {
    "year": 1974, "month": 3, "day": 2, "hour": 8, "minute": 30,
    "gender": "male", "calendar": "solar", "leap_month": False
}
_MEMBER_RESPONSES = {
    401: {"description": "유효한 로그인 Bearer 토큰이 필요합니다."},
    422: {"description": "입력 형식·날짜·윤달 여부·미래 생일을 확인하세요."},
    503: {"description": "회원 저장소 또는 날짜 검증을 사용할 수 없습니다."}
}


def _service(request: Request) -> AuthService:
    return request.app.state.auth_service


def _access_token(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_BEARER)]) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise DomainError("unauthorized", "Authorization: Bearer 로그인 토큰이 필요합니다.", 401)
    return credentials.credentials


def _cookie(response: Response, service: AuthService, provider: SocialProvider, value: str) -> None:
    response.set_cookie(
        cookie_name(provider), value, max_age=STATE_SECONDS, path="/v1/auth",
        secure=service.settings.secure_cookie, httponly=True, samesite="lax"
    )


def social_auth_router() -> APIRouter:
    router = APIRouter(prefix="/v1/auth")

    @router.get("/providers", response_model=ProviderList, tags=[TAG], summary="소셜 로그인 목록·설정 상태")
    def providers(service: Annotated[AuthService, Depends(_service)]):
        return service.providers()

    @router.get("/me", response_model=AuthUser, tags=[TAG], summary="내 회원 정보 · 로그인 필요")
    async def me(
        service: Annotated[AuthService, Depends(_service)],
        access: Annotated[str, Depends(_access_token)]
    ):
        return await service.me(access)

    @router.post("/refresh", response_model=LoginResult, tags=[TAG], summary="로그인 토큰 갱신")
    async def refresh(body: RefreshRequest, service: Annotated[AuthService, Depends(_service)]):
        return await service.refresh(body.refresh_token.get_secret_value())

    @router.post("/logout", response_model=LogoutResult, tags=[TAG], summary="현재 기기 로그아웃")
    async def logout(
        service: Annotated[AuthService, Depends(_service)],
        access: Annotated[str, Depends(_access_token)]
    ):
        await service.logout(access)
        return LogoutResult()

    @router.get(
        "/me/birth", response_model=MemberBirthProfile, tags=[MEMBER_BIRTH_TAG],
        summary="내 사주 입력 정보 조회", description="로그인한 본인의 정보만 조회합니다. 아직 저장하지 않았으면 birth와 updated_at이 null입니다.",
        responses={code: _MEMBER_RESPONSES[code] for code in (401, 503)}
    )
    async def get_birth(
        service: Annotated[AuthService, Depends(_service)],
        access: Annotated[str, Depends(_access_token)]
    ):
        return await service.get_birth(access)

    @router.put(
        "/me/birth", response_model=MemberBirthProfile, tags=[MEMBER_BIRTH_TAG],
        summary="내 사주 정보 최초 저장·전체 수정",
        description="생년월일·한국시간 시/분·성별·양력/음력·윤달 여부를 저장합니다. 전체 입력을 교체하며 처음 요청하면 생성합니다. 음력 날짜는 변환값 대신 입력값을 보관합니다. 잘못된 날짜·존재하지 않는 윤달·미래 생일은422입니다.",
        responses=_MEMBER_RESPONSES
    )
    async def put_birth(
        body: Annotated[Birth, Body(openapi_examples={
            "solar": {"summary": "양력 생일 저장", "value": _BIRTH_EXAMPLE},
            "lunar_leap": {"summary": "음력 윤달 생일 저장", "value": {
                **_BIRTH_EXAMPLE, "year": 2023, "month": 2, "day": 29,
                "calendar": "lunar", "leap_month": True
            }}
        })],
        service: Annotated[AuthService, Depends(_service)],
        access: Annotated[str, Depends(_access_token)]
    ):
        return await service.put_birth(access, body)

    @router.patch(
        "/me/birth", response_model=MemberBirthProfile, tags=[MEMBER_BIRTH_TAG],
        summary="내 사주 정보 일부 수정",
        description="보낸 항목만 기존 값과 합쳐 검증·저장합니다. 0시·0분과 false도 적용합니다. null이나 빈 요청은 허용하지 않습니다. 저장 전이면404 birth_profile_not_found입니다. 날짜·달력·윤달을 바꿀 때는 관련 항목을 함께 보내세요.",
        responses={**_MEMBER_RESPONSES, 404: {"description": "저장된 사주 정보가 없습니다. 먼저 PUT으로 저장하세요."}}
    )
    async def patch_birth(
        body: Annotated[BirthProfilePatch, Body(openapi_examples={
            "time": {"summary": "태어난 시각만 변경", "value": {"hour": 8, "minute": 30}},
            "solar": {"summary": "양력으로 변경", "value": {
                "year": 1974, "month": 3, "day": 2, "calendar": "solar", "leap_month": False
            }}
        })],
        service: Annotated[AuthService, Depends(_service)],
        access: Annotated[str, Depends(_access_token)]
    ):
        return await service.patch_birth(access, body)

    def authorize_endpoint(provider: SocialProvider):
        async def endpoint(response: Response, service: Annotated[AuthService, Depends(_service)]):
            result, cookie = await service.begin(provider)
            _cookie(response, service, provider, cookie)
            return result
        return endpoint

    def login_endpoint(provider: SocialProvider):
        async def endpoint(service: Annotated[AuthService, Depends(_service)]):
            result, cookie = await service.begin(provider)
            response = RedirectResponse(result.authorization_url, status_code=302)
            _cookie(response, service, provider, cookie)
            return response
        return endpoint

    def callback_endpoint(provider: SocialProvider):
        async def endpoint(
            request: Request, response: Response,
            service: Annotated[AuthService, Depends(_service)],
            code: Annotated[str | None, Query(max_length=4096)] = None,
            state: Annotated[str | None, Query(max_length=128)] = None,
            error: Annotated[str | None, Query(max_length=256)] = None
        ):
            result = await service.callback(
                provider, code=code, state=state,
                cookie=request.cookies.get(cookie_name(provider)), error=error
            )
            response.delete_cookie(
                cookie_name(provider), path="/v1/auth", secure=service.settings.secure_cookie,
                httponly=True, samesite="lax"
            )
            return result
        return endpoint

    for provider in SocialProvider:
        name = _NAMES[provider]
        router.add_api_route(
            f"/{provider}/authorize", authorize_endpoint(provider), methods=["GET"],
            response_model=AuthorizationResult, summary=f"{name} 로그인 URL 받기",
            description="반환된 authorization_url을 같은 브라우저에서 열어 로그인합니다. 쿠키를 허용하세요. 앱 설정이 없으면503 social_not_configured입니다.",
            operation_id=f"{provider}_authorization_url", tags=[TAG]
        )
        router.add_api_route(
            f"/{provider}/login", login_endpoint(provider), methods=["GET"],
            response_class=RedirectResponse, status_code=302, summary=f"{name} 로그인 시작 · 브라우저 이동",
            description=f"브라우저 주소창에서 /v1/auth/{provider}/login을 열면 로그인 화면으로 이동합니다. Swagger에서 URL만 받으려면 위의 로그인 URL 받기를 사용하세요.",
            operation_id=f"{provider}_browser_login", tags=[TAG]
        )
        router.add_api_route(
            f"/{provider}/callback", callback_endpoint(provider), methods=["GET"],
            response_model=LoginResult, summary=f"{name} 로그인 완료 · 회원 생성·토큰 발급",
            description="제공자가 자동 호출하는 경로입니다. 최초 로그인은 회원을 생성합니다. 같은 브라우저의 일회성 로그인 요청이 필요합니다. 토큰을 URL에 붙이거나 외부로 전달하지 마세요.",
            operation_id=f"{provider}_login_callback", tags=[TAG]
        )
    return router
