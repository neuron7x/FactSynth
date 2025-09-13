import importlib

import pytest
from fastapi import HTTPException

from factsynth_ultimate.api import routers

# Allow unrequested HTTPX mocks registered by the autouse fixture.
pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def reload_routers(monkeypatch, hosts: str):
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", hosts)
    return importlib.reload(routers)


def test_validate_callback_url_basic(monkeypatch):
    module = reload_routers(monkeypatch, "example.com")
    assert module.validate_callback_url("https://example.com") is None
    with pytest.raises(HTTPException):
        module.validate_callback_url("ftp://example.com")


def test_validate_callback_url_allowed_hosts(monkeypatch):
    module = reload_routers(monkeypatch, "a.com,b.com")
    assert module.validate_callback_url("https://a.com/path") is None
    with pytest.raises(HTTPException):
        module.validate_callback_url("https://c.com")


def test_validate_callback_url_missing_host(monkeypatch):
    module = reload_routers(monkeypatch, "example.com")
    with pytest.raises(HTTPException):
        module.validate_callback_url("https:///path")


def test_validate_callback_url_without_whitelist(monkeypatch):
    module = reload_routers(monkeypatch, "")
    with pytest.raises(HTTPException):
        module.validate_callback_url("https://example.com")
