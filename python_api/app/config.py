from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    ai_provider: Literal["openai", "bedrock"] = "openai"
    bedrock_model_id: str = ""
    bedrock_region: str = ""
    bedrock_auth_mode: Literal["iam", "api_key"] = "iam"
    bedrock_account_id: str = Field(default="", pattern=r"^(?:[0-9]{12})?$")
    bedrock_max_tokens: int = Field(default=8192, ge=256, le=16384)
    ai_daily_call_limit: int = Field(default=100, ge=1, le=100)
    openai_api_key: SecretStr | None = None
    openai_model: str = ""
    ai_timeout_seconds: float = Field(default=45, gt=0, le=180)
    ai_max_concurrency: int = Field(default=4, ge=1, le=32)
    api_key: SecretStr | None = None


def get_settings() -> Settings:
    return Settings()
