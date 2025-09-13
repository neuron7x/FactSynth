import pytest
from fastapi import HTTPException

from factsynth_ultimate.api.routers import validate_callback_url


def test_validate_callback_url_localhost_only(monkeypatch, httpx_mock):
    httpx_mock.reset()
    monkeypatch.delenv("CALLBACK_URL_ALLOWED_HOSTS", raising=False)
    assert validate_callback_url("http://localhost") is None
    with pytest.raises(HTTPException):
        validate_callback_url("https://example.com")
    with pytest.raises(HTTPException):
        validate_callback_url("ftp://localhost")


def test_validate_callback_url_allowed_hosts(monkeypatch, httpx_mock):
    httpx_mock.reset()
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "a.com,b.com")
    assert validate_callback_url("https://a.com/path") is None
    with pytest.raises(HTTPException):
        validate_callback_url("https://c.com")


def test_validate_callback_url_empty_whitelist(monkeypatch, httpx_mock):
    httpx_mock.reset()
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "")
    with pytest.raises(HTTPException):
        validate_callback_url("https://example.com")
