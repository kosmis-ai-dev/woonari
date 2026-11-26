"""CR-022 / T-042: social login requests, public users and session tokens."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from pydantic import ConfigDict, Field, SecretStr, model_validator

from app.models import Birth, Model


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


class MemberBirthProfile(Model):
    model_config = ConfigDict(title="내 사주 입력 정보")
    birth: Birth | None = Field(default=None, description="저장 전에는 null입니다. 음력은 입력한 날짜와 윤달 여부를 그대로 반환합니다.")
    updated_at: int | None = Field(default=None, description="마지막 저장 시각(Unix 초)입니다. 저장 전에는 null입니다.")


class BirthProfilePatch(Model):
    model_config = ConfigDict(title="내 사주 정보 일부 수정")
    year: int = Field(default=None, strict=True, ge=1900, le=2050, description="수정할 출생 연도. 생략하면 기존 값을 유지합니다.")
    month: int = Field(default=None, strict=True, ge=1, le=12)
    day: int = Field(default=None, strict=True, ge=1, le=31)
    hour: int = Field(default=None, strict=True, ge=0, le=23)
    minute: int = Field(default=None, strict=True, ge=0, le=59)
    gender: Literal["male", "female"] = Field(default=None)
    calendar: Literal["solar", "lunar"] = Field(default=None)
    leap_month: bool = Field(default=None, strict=True)

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set:
            raise ValueError("수정할 항목을 하나 이상 입력하세요.")
        return self


@dataclass(frozen=True)
class StoredLogin:
    user: AuthUser
    is_new_user: bool
    refresh_expires_at: int


@dataclass(frozen=True)
class OAuthAttempt:
    code_verifier: str
    nonce: str
