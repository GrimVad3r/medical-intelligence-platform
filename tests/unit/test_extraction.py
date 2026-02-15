"""Unit tests for extraction."""
from src.extraction.message_parser import parse_message


def test_parse_message():
    raw = {"message": "  hello  world  ", "id": 1}
    out = parse_message(raw)
    assert out["text"] == "hello world"
    assert out["external_id"] == "1"
