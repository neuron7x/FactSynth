import importlib

import pytest
from fastapi import HTTPException

from factsynth_ultimate.api import routers


def test_validate_callback_url_basic(monkeypatch, httpx_mock):
    httpx_mock.reset()
    monkeypatch.delenv("CALLBACK_URL_ALLOWED_HOSTS", raising=False)
    importlib.reload(routers)
    assert routers.validate_callback_url("https://example.com") is None
    with pytest.raises(HTTPException):
        routers.validate_callback_url("ftp://example.com")


def test_validate_callback_url_allowed_hosts(monkeypatch, httpx_mock):
    httpx_mock.reset()
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "a.com,b.com")
    importlib.reload(routers)
    assert routers.validate_callback_url("https://a.com/path") is None
    with pytest.raises(HTTPException):
        routers.validate_callback_url("https://c.com")
