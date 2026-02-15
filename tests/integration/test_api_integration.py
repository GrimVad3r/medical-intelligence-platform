"""Integration test: API analyze endpoint."""
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_nlp_analyze():
    r = client.post("/nlp/analyze", json={"text": "Patient has headache."})
    assert r.status_code == 200
    data = r.json()
    assert "entities" in data and "category" in data
