import pytest
from fastapi import HTTPException

from factsynth_ultimate.api import routers
from factsynth_ultimate.api.routers import validate_callback_url


pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_validate_callback_url_basic(httpx_mock):
    httpx_mock.reset()
    validate_callback_url("https://example.com")
    with pytest.raises(HTTPException) as exc:
        validate_callback_url("ftp://example.com")
    assert exc.value.detail == "Disallowed callback URL scheme"


def test_validate_callback_url_allowed_hosts(monkeypatch, httpx_mock):
    httpx_mock.reset()
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "a.com,b.com")
    validate_callback_url("https://a.com/path")
    with pytest.raises(HTTPException) as exc:
        validate_callback_url("https://c.com")
    assert exc.value.detail == "Disallowed callback URL host"


def test_validate_callback_url_missing_host(httpx_mock):
    httpx_mock.reset()
    with pytest.raises(HTTPException) as exc:
        validate_callback_url("https:///path")
    assert exc.value.detail == "Missing callback URL host"


def test_validate_callback_url_dynamic_allowlist(monkeypatch, httpx_mock):
    httpx_mock.reset()

    monkeypatch.setattr(routers, "_get_allowed_hosts", lambda: {"a.com"})
    routers.validate_callback_url("https://a.com/path")

    monkeypatch.setattr(routers, "_get_allowed_hosts", lambda: {"b.com"})
    with pytest.raises(HTTPException) as exc:
        routers.validate_callback_url("https://a.com/path")
    assert exc.value.detail == "Disallowed callback URL host"
    routers.validate_callback_url("https://b.com/path")
