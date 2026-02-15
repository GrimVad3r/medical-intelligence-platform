"""Integration test: extraction parser."""
from src.extraction.message_parser import parse_message


def test_parse_pipeline():
    raw = {"message": "Test", "id": 1, "channel_id": "ch1"}
    out = parse_message(raw)
    assert out["text"] == "Test" and out["channel_id"] == "ch1"
