"""Data validation for messages and NLP/YOLO outputs."""

import re
from typing import Any


def validate_message_text(text: str | None) -> str:
    """Return cleaned text or empty string."""
    if text is None:
        return ""
    s = re.sub(r"\s+", " ", str(text).strip())
    return s[:50000]  # cap length


def validate_entities(entities: list[dict] | dict) -> list[dict]:
    """Ensure entities is a list of dicts with expected keys."""
    if isinstance(entities, dict):
        entities = list(entities.values()) if entities else []
    if not isinstance(entities, list):
        return []
    return [e for e in entities if isinstance(e, dict)]
