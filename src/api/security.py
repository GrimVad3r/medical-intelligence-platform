"""API security dependencies."""

from fastapi import Header, HTTPException

from src.config import get_settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    keys = settings.api_keys
    if not keys:
        return
    if x_api_key is None or x_api_key not in keys:
        raise HTTPException(status_code=401, detail="invalid api key")
