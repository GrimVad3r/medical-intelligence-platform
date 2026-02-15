"""Unit tests for utils."""
from src.transformation.cleaner import clean_text
from src.transformation.validators import validate_message_text


def test_clean_text():
    assert clean_text("  a  b  ") == "a b"


def test_validate_message_text():
    assert validate_message_text("x") == "x"
    assert validate_message_text(None) == ""
