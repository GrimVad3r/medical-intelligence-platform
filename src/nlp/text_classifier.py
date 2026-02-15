"""Medical text classification."""

from typing import Any


def classify(text: str, model=None) -> dict[str, Any]:
    """Return category and confidence. E.g. {category: 'product', confidence: 0.85}."""
    if not text or not text.strip():
        return {"category": "unknown", "confidence": 0.0}
    # Placeholder: integrate transformer or sklearn classifier
    return {"category": "general", "confidence": 0.9}
