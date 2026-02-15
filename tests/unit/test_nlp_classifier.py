"""Unit tests for text classifier."""
from src.nlp.text_classifier import classify


def test_classify_empty():
    out = classify("")
    assert out["category"] == "unknown"
    assert out["confidence"] == 0.0


def test_classify_returns_category():
    out = classify("Patient has fever.")
    assert "category" in out and "confidence" in out
