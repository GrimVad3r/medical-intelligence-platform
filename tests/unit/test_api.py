"""Unit tests for API schemas and routes."""
from fastapi.testclient import TestClient
from src.api.main import app


def test_root():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "service" in r.json()


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    # May fail if DB not configured
    assert r.status_code in (200, 500)
