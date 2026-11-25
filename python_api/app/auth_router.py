"""CR-022 / T-042: browser OAuth and Bearer session endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth_models import (
    AuthorizationResult,
    AuthUser,
    LoginResult,
    LogoutResult,
    ProviderList,
    RefreshRequest,
    SocialProvider,
)
from app.auth_service import STATE_SECONDS, AuthService, cookie_name
from app.errors import DomainError

TAG = "소셜 로그인 · 카카오·구글·네이버"
_BEARER = HTTPBearer(auto_error=False, description="소셜 로그인에서 받은 access_token을 입력합니다.")
_NAMES = {SocialProvider.kakao: "카카오", SocialProvider.google: "구글", SocialProvider.naver: "네이버"}


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
    router = APIRouter(prefix="/v1/auth", tags=[TAG])

    @router.get("/providers", response_model=ProviderList, summary="소셜 로그인 목록·설정 상태")
    def providers(service: Annotated[AuthService, Depends(_service)]):
        return service.providers()

    @router.get("/me", response_model=AuthUser, summary="내 회원 정보 · 로그인 필요")
    async def me(
        service: Annotated[AuthService, Depends(_service)],
        access: Annotated[str, Depends(_access_token)]
    ):
        return await service.me(access)

    @router.post("/refresh", response_model=LoginResult, summary="로그인 토큰 갱신")
    async def refresh(body: RefreshRequest, service: Annotated[AuthService, Depends(_service)]):
        return await service.refresh(body.refresh_token.get_secret_value())

    @router.post("/logout", response_model=LogoutResult, summary="현재 기기 로그아웃")
    async def logout(
        service: Annotated[AuthService, Depends(_service)],
        access: Annotated[str, Depends(_access_token)]
    ):
        await service.logout(access)
        return LogoutResult()

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
            operation_id=f"{provider}_authorization_url"
        )
        router.add_api_route(
            f"/{provider}/login", login_endpoint(provider), methods=["GET"],
            response_class=RedirectResponse, status_code=302, summary=f"{name} 로그인 시작 · 브라우저 이동",
            description=f"브라우저 주소창에서 /v1/auth/{provider}/login을 열면 로그인 화면으로 이동합니다. Swagger에서 URL만 받으려면 위의 로그인 URL 받기를 사용하세요.",
            operation_id=f"{provider}_browser_login"
        )
        router.add_api_route(
            f"/{provider}/callback", callback_endpoint(provider), methods=["GET"],
            response_model=LoginResult, summary=f"{name} 로그인 완료 · 회원 생성·토큰 발급",
            description="제공자가 자동 호출하는 경로입니다. 최초 로그인은 회원을 생성합니다. 같은 브라우저의 일회성 로그인 요청이 필요합니다. 토큰을 URL에 붙이거나 외부로 전달하지 마세요.",
            operation_id=f"{provider}_login_callback"
        )
    return router
