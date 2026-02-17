from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.api.security import require_api_key


def test_api_key_disabled(monkeypatch):
    monkeypatch.setattr("src.api.security.get_settings", lambda: SimpleNamespace(api_keys=[]))
    require_api_key(None)


def test_api_key_rejected(monkeypatch):
    monkeypatch.setattr("src.api.security.get_settings", lambda: SimpleNamespace(api_keys=["abc"]))
    with pytest.raises(HTTPException) as exc:
        require_api_key(None)
    assert exc.value.status_code == 401


def test_api_key_accepted(monkeypatch):
    monkeypatch.setattr("src.api.security.get_settings", lambda: SimpleNamespace(api_keys=["abc"]))
    require_api_key("abc")
