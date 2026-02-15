"""Text and data cleaning."""

import re


def clean_text(text: str) -> str:
    """Normalize whitespace and remove control chars."""
    if not text:
        return ""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return re.sub(r"\s+", " ", text).strip()
