"""Test fixtures and factories."""

import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_message_dict():
    return {
        "channel_id": "test_ch",
        "external_id": "123",
        "text": "Sample medical message.",
        "date": "2024-01-01T00:00:00",
    }
