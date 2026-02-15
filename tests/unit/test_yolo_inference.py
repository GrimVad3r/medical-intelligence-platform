"""Unit tests for YOLO inference."""
from src.yolo.postprocess import postprocess_results


def test_postprocess_empty():
    assert postprocess_results([]) == []


def test_postprocess_returns_list():
    assert isinstance(postprocess_results([None]), list)
