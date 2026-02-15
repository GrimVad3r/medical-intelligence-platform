"""Model explainability entry point for YOLO."""

from src.yolo.yolo_shap_explainer import explain_detection

__all__ = ["explain_detection"]
