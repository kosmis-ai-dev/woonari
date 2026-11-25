"""CR-022 / T-042: social login, one-use attempts and opaque service sessions."""

import hashlib
import re
import secrets
import time
from collections.abc import Callable

from fastapi.concurrency import run_in_threadpool

from app.auth_models import (
    AuthorizationResult,
    AuthUser,
    LoginResult,
    ProviderInfo,
    ProviderList,
    SocialProvider,
    StoredLogin,
)
from app.auth_providers import SocialOAuthGateway
from app.auth_settings import AuthSettings
from app.auth_store import AuthStore
from app.errors import DomainError

ACCESS_SECONDS = 15 * 60
REFRESH_SECONDS = 30 * 24 * 60 * 60
STATE_SECONDS = 10 * 60
_OPAQUE = re.compile(r"[A-Za-z0-9_-]{40,128}\Z")
_NAMES = {SocialProvider.kakao: "카카오", SocialProvider.google: "구글", SocialProvider.naver: "네이버"}


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def cookie_name(provider: SocialProvider) -> str:
    return f"woonari_oauth_{provider}"


def _token(prefix: str) -> str:
    return prefix + secrets.token_urlsafe(32)


def _valid_token(value: str, prefix: str) -> bool:
    return value.startswith(prefix) and bool(_OPAQUE.fullmatch(value[len(prefix):]))


class AuthService:
    def __init__(
        self, settings: AuthSettings, store: AuthStore, gateway: SocialOAuthGateway,
        *, clock: Callable[[], int] | None = None
    ):
        self.settings = settings
        self.store = store
        self.gateway = gateway
        self.clock = clock or (lambda: int(time.time()))

    def providers(self) -> ProviderList:
        return ProviderList(items=[
            ProviderInfo(
                provider=provider, name=_NAMES[provider], configured=self.settings.configured(provider),
                login_path=f"/v1/auth/{provider}/login", authorize_path=f"/v1/auth/{provider}/authorize",
                callback_url=self.settings.callback_url(provider)
            )
            for provider in SocialProvider
        ])

    def _configured(self, provider: SocialProvider) -> tuple[str, str]:
        if not self.settings.configured(provider):
            raise DomainError("social_not_configured", f"{_NAMES[provider]} 로그인 앱 설정이 필요합니다.", 503)
        return self.settings.credentials(provider)

    async def begin(self, provider: SocialProvider) -> tuple[AuthorizationResult, str]:
        client_id, _ = self._configured(provider)
        state, cookie = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        verifier, nonce = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
        now = self.clock()
        url = self.gateway.authorization_url(
            provider, client_id=client_id, redirect_uri=self.settings.callback_url(provider),
            state=state, code_verifier=verifier, nonce=nonce
        )
        await run_in_threadpool(
            self.store.create_state, provider=provider, state_hash=token_hash(state),
            cookie_hash=token_hash(cookie), code_verifier=verifier, nonce=nonce,
            now=now, expires_at=now + STATE_SECONDS
        )
        return AuthorizationResult(authorization_url=url, expires_in=STATE_SECONDS), cookie

    async def callback(
        self, provider: SocialProvider, *, code: str | None, state: str | None,
        cookie: str | None, error: str | None = None
    ) -> LoginResult:
        client_id, client_secret = self._configured(provider)
        if not state or not cookie or not _OPAQUE.fullmatch(state) or not _OPAQUE.fullmatch(cookie):
            raise DomainError("oauth_state_invalid", "로그인 요청이 만료되었거나 유효하지 않습니다. 다시 시작하세요.", 400)
        attempt = await run_in_threadpool(
            self.store.consume_state, provider=provider, state_hash=token_hash(state),
            cookie_hash=token_hash(cookie), now=self.clock()
        )
        if error:
            raise DomainError("social_access_denied", "소셜 로그인이 취소되었거나 허용되지 않았습니다.", 400)
        if not code or len(code) > 4096 or any(ord(char) < 33 for char in code):
            raise DomainError("social_login_failed", "로그인 인증 코드를 확인할 수 없습니다.", 400)
        identity = await self.gateway.exchange(
            provider, client_id=client_id, client_secret=client_secret,
            redirect_uri=self.settings.callback_url(provider), code=code, state=state,
            code_verifier=attempt.code_verifier, nonce=attempt.nonce
        )
        if identity.provider != provider:
            raise DomainError("social_login_failed", "로그인 사용자 정보를 확인할 수 없습니다.", 401)
        now = self.clock()
        access, refresh = _token("wn_at_"), _token("wn_rt_")
        login = await run_in_threadpool(
            self.store.login, identity, access_hash=token_hash(access), refresh_hash=token_hash(refresh),
            access_expires_at=now + ACCESS_SECONDS, refresh_expires_at=now + REFRESH_SECONDS, now=now
        )
        return self._result(login, access, refresh, now)

    def _result(self, login: StoredLogin, access: str, refresh: str, now: int) -> LoginResult:
        return LoginResult(
            access_token=access, refresh_token=refresh,
            expires_in=min(ACCESS_SECONDS, max(0, login.refresh_expires_at - now)),
            refresh_expires_in=max(0, login.refresh_expires_at - now),
            is_new_user=login.is_new_user, user=login.user
        )

    async def me(self, access_token: str) -> AuthUser:
        if not _valid_token(access_token, "wn_at_"):
            raise DomainError("unauthorized", "유효한 로그인 토큰이 필요합니다.", 401)
        return await run_in_threadpool(self.store.authenticate, token_hash(access_token), now=self.clock())

    async def refresh(self, refresh_token: str) -> LoginResult:
        if not _valid_token(refresh_token, "wn_rt_"):
            raise DomainError("unauthorized", "유효한 갱신 토큰이 필요합니다.", 401)
        now = self.clock()
        access, refresh = _token("wn_at_"), _token("wn_rt_")
        login = await run_in_threadpool(
            self.store.rotate_refresh, token_hash(refresh_token), access_hash=token_hash(access),
            new_refresh_hash=token_hash(refresh), access_expires_at=now + ACCESS_SECONDS, now=now
        )
        return self._result(login, access, refresh, now)

    async def logout(self, access_token: str) -> None:
        await self.me(access_token)
        await run_in_threadpool(self.store.logout, token_hash(access_token), now=self.clock())
