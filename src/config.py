"""Configuration management via environment and pydantic-settings."""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Environment: development | staging | production
    environment: str = "development"

    database_url: str = "postgresql://localhost:5432/medical_intel"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout: int = 30

    telegram_api_id: str | None = None
    telegram_api_hash: str | None = None
    telegram_session_string: str | None = None
    telegram_channels: List[str] = []

    @field_validator("telegram_channels", mode="before")
    @classmethod
    def parse_channels(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v or []

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["*"]
    api_rate_limit: str | None = None  # e.g. "100/minute"

    log_level: str = "INFO"
    log_format: str = "text"  # text | json
    log_path: str | None = None  # optional file path

    sentry_dsn: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v if v is not None else ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
