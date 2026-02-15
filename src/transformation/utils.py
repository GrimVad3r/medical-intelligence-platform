"""Transformation utilities."""

from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def safe_json(o: Any) -> Any:
    """Convert to JSON-serializable form."""
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, dict):
        return {k: safe_json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [safe_json(x) for x in o]
    return o
