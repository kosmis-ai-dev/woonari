"""CR-022 / T-042: social login requests, public users and session tokens."""

from dataclasses import dataclass
from enum import StrEnum

from pydantic import Field, SecretStr

from app.models import Model


class SocialProvider(StrEnum):
    kakao = "kakao"
    google = "google"
    naver = "naver"


@dataclass(frozen=True)
class SocialIdentity:
    provider: SocialProvider
    subject: str
    nickname: str | None = None
    email: str | None = None
    email_verified: bool = False


class AuthUser(Model):
    id: str
    nickname: str | None = None
    email: str | None = None
    email_verified: bool = False
    providers: list[SocialProvider]
    created_at: int


class ProviderInfo(Model):
    provider: SocialProvider
    name: str
    configured: bool
    login_path: str
    authorize_path: str
    callback_url: str


class ProviderList(Model):
    items: list[ProviderInfo]


class AuthorizationResult(Model):
    authorization_url: str
    expires_in: int


class LoginResult(Model):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int
    is_new_user: bool = False
    user: AuthUser


class RefreshRequest(Model):
    refresh_token: SecretStr = Field(min_length=20, max_length=256, description="로그인 또는 갱신에서 받은 refresh_token입니다.")


class LogoutResult(Model):
    logged_out: bool = True


@dataclass(frozen=True)
class StoredLogin:
    user: AuthUser
    is_new_user: bool
    refresh_expires_at: int


@dataclass(frozen=True)
class OAuthAttempt:
    code_verifier: str
    nonce: str
