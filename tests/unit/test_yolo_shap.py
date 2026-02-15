"""Unit tests for YOLO SHAP."""
from src.yolo.yolo_shap_explainer import explain_detection


def test_explain_detection_returns_dict():
    out = explain_detection("/fake/path.jpg", [0, 0, 10, 10])
    assert isinstance(out, dict)
