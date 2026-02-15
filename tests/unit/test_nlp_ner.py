"""Unit tests for NLP NER."""
import pytest
from src.nlp.medical_ner import extract_entities


def test_extract_entities_empty():
    assert extract_entities("") == {"DRUG": [], "CONDITION": [], "DOSAGE": []}


def test_extract_entities_returns_dict():
    out = extract_entities("Some text")
    assert isinstance(out, dict)
    assert "DRUG" in out and "CONDITION" in out
