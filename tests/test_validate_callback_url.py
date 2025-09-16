from http import HTTPStatus

import pytest

from factsynth_ultimate.api.routers import get_allowed_hosts, reload_allowed_hosts
from factsynth_ultimate.validators.callback import validate_callback_url

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_validate_callback_url_disallowed_scheme():
    problem = validate_callback_url("ftp://example.com", ["example.com"])
    assert problem is not None
    assert problem.status == HTTPStatus.BAD_REQUEST
    assert "scheme" in problem.detail.lower()
    assert problem.extras == {
        "reason": "scheme_not_allowed",
        "allowed_schemes": ["http", "https"],
    }


def test_validate_callback_url_host_mismatch():
    problem = validate_callback_url("https://b.com", ["a.com"])
    assert problem is not None
    assert "b.com" in problem.detail
    assert problem.extras == {
        "reason": "host_not_allowed",
        "host": "b.com",
        "allowed_hosts": ["a.com"],
    }


def test_validate_callback_url_empty_allowlist():
    problem = validate_callback_url("https://example.com", [])
    assert problem is not None
    assert "empty" in problem.detail.lower()
    assert problem.extras == {
        "reason": "allowlist_empty",
    }


def test_validate_callback_url_missing_host():
    problem = validate_callback_url("https:///path", ["a.com"])
    assert problem is not None
    assert "host" in problem.detail.lower()
    assert problem.extras == {"reason": "missing_host"}


def test_validate_callback_url_dynamic_allowlist(monkeypatch):
    reload_allowed_hosts()
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "a.com")
    allowed = get_allowed_hosts()
    assert allowed == ("a.com",)
    assert validate_callback_url("https://a.com/path", allowed) is None

    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "b.com")
    # Cached value remains until reloaded
    assert get_allowed_hosts() == ("a.com",)

    reload_allowed_hosts()
    allowed = get_allowed_hosts()
    assert allowed == ("b.com",)
    assert validate_callback_url("https://b.com/path", allowed) is None


def test_get_allowed_hosts_cache(monkeypatch):
    reload_allowed_hosts()
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "a.com")
    assert get_allowed_hosts() == ("a.com",)

    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "b.com")
    assert get_allowed_hosts() == ("a.com",)

    reload_allowed_hosts()
    assert get_allowed_hosts() == ("b.com",)
