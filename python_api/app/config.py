"""CR-025 / T-045: Python-owned local and deployed application settings."""

import os
from pathlib import Path
from typing import Literal

from dotenv.parser import parse_stream
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, DotEnvSettingsSource, SettingsConfigDict
from pydantic_settings.sources.utils import parse_env_vars

API_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ENV_FILE = API_ROOT / ".env"
# An installed wheel must not discover a shared site-packages .env file.
DEFAULT_ENV_FILE = PYTHON_ENV_FILE if (API_ROOT / "pyproject.toml").is_file() else None


def _literal_env_values(file_path: Path, encoding: str = "utf-8") -> dict[str, str | None]:
    values = {}
    normalized = set()
    with file_path.open(encoding=encoding) as stream:
        for item in parse_stream(stream):
            if item.error:
                raise ValueError("환경설정 파일 형식을 확인하세요.")
            if item.key is None:
                continue
            key = item.key.lower()
            if key in normalized:
                raise ValueError("환경설정 파일의 중복 항목을 확인하세요.")
            normalized.add(key)
            values[item.key] = item.value
    return values


class _LiteralDotEnvSource(DotEnvSettingsSource):
    def _read_env_file(self, file_path: Path):
        values = _literal_env_values(file_path, self.env_file_encoding or "utf-8")
        return parse_env_vars(values, self.case_sensitive, self.env_ignore_empty, self.env_parse_none_str)


def python_env_file(override: Path | None = None) -> Path | None:
    """Select one file without consulting cwd or silently ignoring an override."""
    selected = str(override) if override is not None else os.environ.get("WOONARI_ENV_FILE")
    path = Path(selected) if selected else DEFAULT_ENV_FILE
    if selected is not None and (not selected or not path.is_absolute()):
        raise RuntimeError("WOONARI_ENV_FILE에는 존재하는 전용 설정 파일의 절대 경로가 필요합니다.")
    if path is None:
        return None
    try:
        if not path.exists():
            if selected is not None or path.is_symlink():
                raise ValueError
            return None
        if path.is_symlink() or not path.is_file():
            raise ValueError
        info = path.stat()
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError
        # Check the selected file's directory, including explicit deployment mounts.
        if path.parent.is_symlink():
            raise ValueError
        return path
    except (OSError, ValueError, TypeError):
        raise RuntimeError("Python API 전용 환경설정 파일의 존재·소유자·권한600을 확인하세요.") from None


def python_environment_values(
    env_file: Path | None = None, *, missing_file_ok: bool = False
) -> dict[str, str | None]:
    """Literal file values with process values taking precedence, no secret output."""
    try:
        if env_file is not None and missing_file_ok and not env_file.exists():
            if not env_file.is_absolute() or env_file.is_symlink():
                raise ValueError
            path = None
        else:
            path = python_env_file(env_file)
        values = {} if path is None else {
            key.lower(): value for key, value in _literal_env_values(path).items()
        }
        values.update({key.lower(): value for key, value in os.environ.items()})
        return values
    except (OSError, ValueError, TypeError):
        raise RuntimeError("Python API 환경설정 형식을 확인하세요. 설정값은 출력하지 않습니다.") from None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE, env_file_encoding="utf-8", extra="ignore",
        hide_input_in_errors=True
    )
    ai_provider: Literal["openai", "bedrock"] = "openai"
    bedrock_model_id: str = ""
    bedrock_region: str = ""
    bedrock_auth_mode: Literal["iam", "api_key"] = "iam"
    aws_bearer_token_bedrock: SecretStr = Field(default_factory=lambda: SecretStr(""))
    bedrock_account_id: str = Field(default="", pattern=r"^(?:[0-9]{12})?$")
    bedrock_max_tokens: int = Field(default=8192, ge=256, le=16384)
    ai_daily_call_limit: int = Field(default=100, ge=1, le=100)
    openai_api_key: SecretStr | None = None
    openai_model: str = ""
    ai_timeout_seconds: float = Field(default=45, gt=0, le=180)
    ai_max_concurrency: int = Field(default=4, ge=1, le=32)
    api_key: SecretStr | None = None
    woonari_env: Literal["development", "production", "test"] = "development"
    woonari_state_dir: Path | None = None
    woonari_db_backend: Literal["sqlite", "mysql"] = "sqlite"
    woonari_db_host: str = ""
    woonari_db_port: int = Field(default=3306, ge=1, le=65535)
    woonari_db_name: str = "woonari"
    woonari_db_user: str = ""
    woonari_db_password: SecretStr = Field(default_factory=lambda: SecretStr(""))
    woonari_db_ca_file: Path | None = None
    auth_public_base_url: str = "http://127.0.0.1:9090"
    kakao_client_id: SecretStr = Field(default_factory=lambda: SecretStr(""))
    kakao_client_secret: SecretStr = Field(default_factory=lambda: SecretStr(""))
    google_client_id: SecretStr = Field(default_factory=lambda: SecretStr(""))
    google_client_secret: SecretStr = Field(default_factory=lambda: SecretStr(""))
    naver_client_id: SecretStr = Field(default_factory=lambda: SecretStr(""))
    naver_client_secret: SecretStr = Field(default_factory=lambda: SecretStr(""))

    @field_validator("woonari_state_dir", "woonari_db_ca_file", mode="before")
    @classmethod
    def empty_optional_path(cls, value):
        return None if value == "" else value

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        literal = _LiteralDotEnvSource(
            settings_cls, env_file=dotenv_settings.env_file,
            env_file_encoding=dotenv_settings.env_file_encoding,
            case_sensitive=dotenv_settings.case_sensitive, env_prefix=dotenv_settings.env_prefix,
            env_ignore_empty=dotenv_settings.env_ignore_empty,
            env_parse_none_str=dotenv_settings.env_parse_none_str,
            env_parse_enums=dotenv_settings.env_parse_enums
        )
        return init_settings, env_settings, literal, file_secret_settings


def get_settings() -> Settings:
    try:
        return Settings(_env_file=python_env_file())
    except (OSError, ValueError, TypeError):
        raise RuntimeError("Python API 환경설정 형식과 허용 범위를 확인하세요. 설정값은 출력하지 않습니다.") from None
