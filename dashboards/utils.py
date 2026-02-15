"""Dashboard utilities."""

import httpx
from dashboards.config import API_BASE


def api_get(path: str, params: dict | None = None) -> dict:
    with httpx.Client(base_url=API_BASE, timeout=30) as client:
        r = client.get(path, params=params)
        r.raise_for_status()
        return r.json()
