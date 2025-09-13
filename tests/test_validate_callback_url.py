import pytest
from fastapi import HTTPException

from factsynth_ultimate.api.routers import validate_callback_url


def test_validate_callback_url_basic(httpx_mock):
    httpx_mock.reset()
    assert validate_callback_url("https://example.com") is None
    with pytest.raises(HTTPException):
        validate_callback_url("ftp://example.com")


def test_validate_callback_url_allowed_hosts(monkeypatch, httpx_mock):
    httpx_mock.reset()
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "a.com,b.com")
    assert validate_callback_url("https://a.com/path") is None
    with pytest.raises(HTTPException):
        validate_callback_url("https://c.com")


def test_validate_callback_url_missing_host(httpx_mock):
    httpx_mock.reset()
    with pytest.raises(HTTPException):
        validate_callback_url("https:///path")
