"""Integration test: API analyze endpoint."""
from fastapi.testclient import TestClient

from src.api.main import app
from src.nlp.message_processor import MessageProcessor

client = TestClient(app)


def test_nlp_analyze(monkeypatch):
    monkeypatch.setattr(
        MessageProcessor,
        "process",
        lambda self, text, include_explanations=False: {
            "entities": {"CONDITION": [{"text": "headache"}]},
            "category": "medical",
            "confidence": 0.99,
            "linked_entities": {},
        },
    )
    r = client.post("/nlp/analyze", json={"text": "Patient has headache."})
    assert r.status_code == 200
    data = r.json()
    assert "entities" in data and "category" in data
