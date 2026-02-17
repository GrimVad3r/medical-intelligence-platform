"""SHAP explainability for YOLO / image models."""

from typing import Any


def explain_detection(image_path: str, box: list[float], model=None) -> dict[str, Any]:
    """
    Return SHAP or gradient-based explanation for a YOLO detection.
    Args:
        image_path: Path to the image file
        box: Bounding box coordinates [x1, y1, x2, y2]
        model: YOLO model instance (must support SHAP or gradient-based explainability)
    Returns:
        dict with keys: importance_map (np.ndarray), summary (str)
    """
    import numpy as np
    try:
        if model is None:
            raise ValueError("YOLO model instance required for explainability.")
        # Load image
        import cv2
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Image not found: {image_path}")
        # Crop region of interest
        x1, y1, x2, y2 = map(int, box)
        roi = image[y1:y2, x1:x2]
        # SHAP explainability
        import shap
        explainer = shap.GradientExplainer(model, roi)
        shap_values = explainer.shap_values(roi)
        importance_map = np.mean(shap_values, axis=0)
        summary = "SHAP importance map computed for detection."
        return {"importance_map": importance_map, "summary": summary}
    except Exception as e:
        return {"importance_map": None, "summary": f"Explainability error: {e}"}
