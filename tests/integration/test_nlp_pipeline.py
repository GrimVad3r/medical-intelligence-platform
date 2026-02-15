"""Integration test: full NLP pipeline."""
import pytest
from src.nlp.message_processor import MessageProcessor


def test_message_processor_e2e(sample_text):
    p = MessageProcessor()
    out = p.process(sample_text, include_explanations=False)
    assert "entities" in out and "category" in out
