import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from factsynth_ultimate.api import routers
from factsynth_ultimate.api.routers import reload_allowed_hosts, validate_callback_url

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_validate_callback_url_disallowed_scheme(monkeypatch, httpx_mock):
    httpx_mock.reset()
    monkeypatch.setattr(routers, "get_allowed_hosts", lambda: {"example.com"})
    with pytest.raises(HTTPException) as exc:
        validate_callback_url("ftp://example.com")
    assert exc.value.detail == "Callback URL scheme must be http or https"


def test_validate_callback_url_host_mismatch(monkeypatch, httpx_mock):
    httpx_mock.reset()
    monkeypatch.setattr(routers, "get_allowed_hosts", lambda: {"a.com"})
    with pytest.raises(HTTPException) as exc:
        validate_callback_url("https://b.com")
    assert exc.value.detail == "Callback URL host not in allowlist"


def test_validate_callback_url_empty_allowlist(monkeypatch, httpx_mock):
    httpx_mock.reset()
    monkeypatch.setattr(routers, "get_allowed_hosts", lambda: set())
    with pytest.raises(HTTPException) as exc:
        validate_callback_url("https://example.com")
    assert exc.value.detail == "Callback URL host allowlist is empty"


def test_validate_callback_url_missing_host(monkeypatch, httpx_mock):
    httpx_mock.reset()
    monkeypatch.setattr(routers, "get_allowed_hosts", lambda: {"a.com"})
    with pytest.raises(HTTPException) as exc:
        validate_callback_url("https:///path")
    assert exc.value.detail == "Missing callback URL host"


def test_validate_callback_url_dynamic_allowlist(httpx_mock):
    httpx_mock.reset()
    reload_allowed_hosts()

    env_a = {"CALLBACK_URL_ALLOWED_HOSTS": "a.com"}
    env_b = {"CALLBACK_URL_ALLOWED_HOSTS": "b.com"}

    with patch.dict(os.environ, env_a):
        validate_callback_url("https://a.com/path")

    with patch.dict(os.environ, env_b):
        with pytest.raises(HTTPException) as exc:
            validate_callback_url("https://b.com/path")
        assert exc.value.detail == "Callback URL host not in allowlist"

        reload_allowed_hosts()
        validate_callback_url("https://b.com/path")


def test_get_allowed_hosts_cache(monkeypatch):
    reload_allowed_hosts()
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "a.com")

    # First call caches the environment value
    assert routers.get_allowed_hosts() == {"a.com"}

    # Changing the environment does not affect cached result
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "b.com")
    assert routers.get_allowed_hosts() == {"a.com"}

    # After cache invalidation, new environment value is loaded
    reload_allowed_hosts()
    assert routers.get_allowed_hosts() == {"b.com"}
