import pytest
from fastapi import HTTPException

from factsynth_ultimate.api.routers import validate_callback_url


def test_validate_callback_url_basic(httpx_mock):
    httpx_mock.reset()
    validate_callback_url("https://example.com")
    with pytest.raises(HTTPException):
        validate_callback_url("ftp://example.com")


def test_validate_callback_url_allowed_hosts(monkeypatch, httpx_mock):
    httpx_mock.reset()
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "a.com,b.com")
    validate_callback_url("https://a.com/path")
    with pytest.raises(HTTPException):
        validate_callback_url("https://c.com")
