"""CR-022 / T-042: explicit project-only social application settings."""

import ipaddress
import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values
from pydantic import ConfigDict, Field, SecretStr, field_validator

from app.auth_models import SocialProvider
from app.config import Settings, python_environment_values
from app.config import python_env_file as configured_python_env_file
from app.errors import DomainError
from app.models import Model

PRIVATE_ROOT = Path(__file__).resolve().parents[2] / ".local/woonari"
PROVIDERS_FILE = PRIVATE_ROOT / "auth/providers.env"
_ENV_FIELDS = {
    "AUTH_PUBLIC_BASE_URL": "auth_public_base_url",
    "KAKAO_CLIENT_ID": "kakao_client_id",
    "KAKAO_CLIENT_SECRET": "kakao_client_secret",
    "GOOGLE_CLIENT_ID": "google_client_id",
    "GOOGLE_CLIENT_SECRET": "google_client_secret",
    "NAVER_CLIENT_ID": "naver_client_id",
    "NAVER_CLIENT_SECRET": "naver_client_secret"
}


class AuthSettings(Model):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    auth_public_base_url: str = "http://127.0.0.1:9090"
    kakao_client_id: SecretStr = Field(default_factory=lambda: SecretStr(""))
    kakao_client_secret: SecretStr = Field(default_factory=lambda: SecretStr(""))
    google_client_id: SecretStr = Field(default_factory=lambda: SecretStr(""))
    google_client_secret: SecretStr = Field(default_factory=lambda: SecretStr(""))
    naver_client_id: SecretStr = Field(default_factory=lambda: SecretStr(""))
    naver_client_secret: SecretStr = Field(default_factory=lambda: SecretStr(""))

    @field_validator("auth_public_base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in {"", "/"}
            or any(ord(char) < 33 for char in value)
        ):
            raise ValueError("로그인 서버 주소를 확인하세요.")
        if parsed.scheme == "http" and (
            parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.port != 9090
        ):
            raise ValueError("개발용 loopback 9090 외에는 HTTPS가 필요합니다.")
        return value.rstrip("/")

    @field_validator(
        "kakao_client_id", "kakao_client_secret", "google_client_id",
        "google_client_secret", "naver_client_id", "naver_client_secret"
    )
    @classmethod
    def validate_credential(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if len(raw) > 2048 or any(ord(char) < 33 for char in raw):
            raise ValueError("소셜 앱 설정 형식을 확인하세요.")
        return value

    def credentials(self, provider: SocialProvider) -> tuple[str, str]:
        return (
            getattr(self, f"{provider}_client_id").get_secret_value(),
            getattr(self, f"{provider}_client_secret").get_secret_value()
        )

    def configured(self, provider: SocialProvider) -> bool:
        return all(self.credentials(provider))

    def callback_url(self, provider: SocialProvider) -> str:
        return f"{self.auth_public_base_url}/v1/auth/{provider}/callback"

    @property
    def secure_cookie(self) -> bool:
        return urlsplit(self.auth_public_base_url).scheme == "https"


def load_auth_settings(path: Path = PROVIDERS_FILE) -> AuthSettings:
    """Never consult ambient provider credentials or another project's env."""
    if not path.exists():
        return AuthSettings()
    try:
        if path.is_symlink() or not path.is_file():
            raise ValueError
        if path.is_relative_to(PRIVATE_ROOT.parent):
            current = PRIVATE_ROOT.parent
            if current.is_symlink():
                raise ValueError
            for component in path.relative_to(current).parts:
                current /= component
                if current.is_symlink():
                    raise ValueError
        elif path.parent.is_symlink():
            raise ValueError
        info = path.stat()
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError
        values = dotenv_values(path, interpolate=False)
        if not set(values) <= set(_ENV_FIELDS) or any(value is None for value in values.values()):
            raise ValueError
        return AuthSettings(**{_ENV_FIELDS[key]: value for key, value in values.items()})
    except (OSError, ValueError, TypeError):
        raise DomainError("auth_configuration_invalid", "소셜 로그인 전용 설정을 확인하세요.", 503) from None


def auth_settings_from_python(settings: Settings) -> AuthSettings:
    """Copy only social settings; AI/database secrets are never mixed into auth."""
    try:
        return AuthSettings(**{field: getattr(settings, field) for field in _ENV_FIELDS.values()})
    except (ValueError, TypeError):
        raise RuntimeError("소셜 로그인 Python 환경설정 형식을 확인하세요.") from None


def validate_production_auth(settings: Settings, auth: AuthSettings) -> None:
    if settings.woonari_env != "production":
        return
    if not all(auth.configured(provider) for provider in SocialProvider):
        raise RuntimeError("운영 소셜 로그인에는 세 제공자의 Client ID와 Client secret 설정이 모두 필요합니다.")
    parsed = urlsplit(auth.auth_public_base_url)
    host = (parsed.hostname or "").lower().rstrip(".")
    local = host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost")
    try:
        address = ipaddress.ip_address(host)
        local = local or address.is_loopback or address.is_unspecified
    except ValueError:
        pass
    if parsed.scheme != "https" or local:
        raise RuntimeError("운영 소셜 로그인에는 공개 HTTPS AUTH_PUBLIC_BASE_URL이 필요합니다.")


def load_local_auth_settings(
    *, python_env_file: Path | None = None, legacy_file: Path | None = None
) -> AuthSettings:
    """Prefer the complete Python auth source, or use the legacy file as a unit."""
    values = python_environment_values(python_env_file, missing_file_ok=True)
    selected = {field: values[field] for field in _ENV_FIELDS.values() if field in values}
    if not selected:
        return load_auth_settings(legacy_file if legacy_file is not None else PROVIDERS_FILE)
    try:
        return AuthSettings(**selected)
    except (ValueError, TypeError):
        raise RuntimeError("소셜 로그인 Python 환경설정 형식을 확인하세요.") from None


def local_auth_source(*, python_env_file: Path | None = None, legacy_file: Path | None = None) -> str:
    """Return source metadata only; process values may override file values."""
    keys = set(_ENV_FIELDS.values())
    if any(key.lower() in keys for key in os.environ):
        return "environment"
    values = python_environment_values(python_env_file, missing_file_ok=True)
    if keys.intersection(values):
        return str(configured_python_env_file(python_env_file))
    return str(legacy_file if legacy_file is not None else PROVIDERS_FILE)
