"""Unit tests for API schemas and routes."""
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.middleware import parse_rate_limit


def test_root():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "service" in r.json()


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["database"] in ("ok", "error")


def test_metrics_endpoint():
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")


def test_rate_limit_parser():
    assert parse_rate_limit("100/minute") == (100, 60)


def test_trends_validation():
    client = TestClient(app)
    r = client.get("/trends?granularity=year")
    assert r.status_code == 422
