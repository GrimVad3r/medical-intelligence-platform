"""Parse and normalize Telegram messages."""

import re
from typing import Any


def parse_message(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw Telegram message to a standard shape."""
    text = raw.get("message") or raw.get("text") or ""
    text = re.sub(r"\s+", " ", text).strip()
    return {
        "channel_id": raw.get("channel_id", ""),
        "external_id": str(raw.get("id", raw.get("external_id", ""))),
        "text": text,
        "date": raw.get("date"),
        "media": raw.get("media"),
        "entities": raw.get("entities"),
    }
