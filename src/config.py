"""Configuration management via environment and pydantic-settings."""

from functools import lru_cache
from typing import List, Any, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str 
    database_pool_size: int = 20 
    database_max_overflow: int = 40 

    # Telegram Credentials
    telegram_api_id: int 
    telegram_api_hash: str 
    telegram_channels: Any = []

    # Telegram Proxy Configuration
    telegram_proxy_addr: str | None = None 
    telegram_proxy_port: int | None = None 
    telegram_proxy_secret: str | None = None 

    @field_validator("telegram_channels", mode="before")
    @classmethod
    def parse_channels(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            # Split by comma and clean up whitespace
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
