"""SHAP explainability for YOLO / image models."""

from typing import Any


def explain_detection(image_path: str, box: list[float], model=None) -> dict[str, Any]:
    """Return SHAP or gradient-based explanation for a detection."""
    return {"importance_map": None, "summary": "Not implemented"}
