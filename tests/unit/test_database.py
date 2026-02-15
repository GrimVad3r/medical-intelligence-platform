"""Unit tests for database (models, no real DB)."""
from src.database.models import Message, NLPResult, Product


def test_message_model_fields():
    assert hasattr(Message, "id") and hasattr(Message, "text") and hasattr(Message, "channel_id")


def test_nlp_result_model():
    assert hasattr(NLPResult, "message_id") and hasattr(NLPResult, "entities")


def test_product_model():
    assert hasattr(Product, "name") and hasattr(Product, "category")
