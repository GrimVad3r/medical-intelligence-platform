"""Unit tests for NLP SHAP."""
from src.nlp.shap_explainer import explain


def test_explain_returns_dict():
    out = explain("test")
    assert isinstance(out, dict)
    assert "feature_importance" in out
