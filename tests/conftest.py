"""Pytest configuration and fixtures."""

import os
import pytest

# Use in-memory SQLite for unit tests if DB tests are enabled
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture
def sample_text():
    return "Patient presented with hypertension and prescribed Lisinopril 10mg."


@pytest.fixture
def sample_entities():
    return {"DRUG": [{"text": "Lisinopril", "start": 0, "end": 10}], "CONDITION": [], "DOSAGE": []}
