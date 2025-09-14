import string

import pytest
from fastapi import HTTPException

from factsynth_ultimate.api import routers
from factsynth_ultimate.api.routers import validate_callback_url

try:
    from hypothesis import HealthCheck, assume, given, settings
    from hypothesis import strategies as st
except ModuleNotFoundError:  # pragma: no cover - optional
    pytest.skip("hypothesis not installed", allow_module_level=True)


@pytest.fixture(autouse=True)
def _no_httpx_assert(httpx_mock):
    yield
    httpx_mock.reset(assert_all_responses_were_requested=False)


# Strategies -----------------------------------------------------------------


def _idn_labels() -> st.SearchStrategy[str]:
    """Generate individual IDN labels without dots or whitespace."""
    alphabet = st.characters(categories=["Lu", "Ll", "Lo", "Nd"])
    return st.text(alphabet=alphabet, min_size=1, max_size=10)


def _idn_hosts() -> st.SearchStrategy[str]:
    return st.lists(_idn_labels(), min_size=2, max_size=3).map(".".join)


def _ascii_hosts() -> st.SearchStrategy[str]:
    label = st.text(alphabet=string.ascii_lowercase + string.digits + "-", min_size=1, max_size=10)
    return st.lists(label, min_size=2, max_size=3).map(".".join)


def _ipv6_hosts() -> st.SearchStrategy[str]:
    return st.ip_addresses(v=6).map(lambda ip: ip.compressed)


HOSTS = st.one_of(_ascii_hosts(), _idn_hosts(), _ipv6_hosts())
PORTS = st.integers(min_value=1, max_value=65535).filter(lambda p: p not in (80, 443))
SCHEMES = st.sampled_from(sorted(routers.ALLOWED_CALLBACK_SCHEMES))


# Tests ----------------------------------------------------------------------


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(scheme=SCHEMES, host=HOSTS, port=PORTS)
def test_valid_random_urls(monkeypatch, scheme: str, host: str, port: int) -> None:
    """Allowed scheme/host combinations should pass validation."""
    monkeypatch.setattr(routers, "get_allowed_hosts", lambda: {host.lower()})
    netloc = f"[{host}]" if ":" in host else host
    url = f"{scheme}://{netloc}:{port}/cb"
    validate_callback_url(url)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    scheme=st.text(alphabet=string.ascii_lowercase, min_size=3, max_size=8).filter(
        lambda s: s not in routers.ALLOWED_CALLBACK_SCHEMES
    ),
    host=HOSTS,
    port=PORTS,
)
def test_rejects_disallowed_schemes(monkeypatch, scheme: str, host: str, port: int) -> None:
    """Any scheme outside the allowlist must raise HTTPException."""
    monkeypatch.setattr(routers, "get_allowed_hosts", lambda: {host.lower()})
    netloc = f"[{host}]" if ":" in host else host
    url = f"{scheme}://{netloc}:{port}/cb"
    with pytest.raises(HTTPException):
        validate_callback_url(url)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    scheme=SCHEMES,
    allowed_host=HOSTS,
    other_host=HOSTS,
    port=PORTS,
)
def test_rejects_disallowed_hosts(
    monkeypatch, scheme: str, allowed_host: str, other_host: str, port: int
) -> None:
    """Hosts not in the allowlist should trigger HTTPException."""
    assume(allowed_host != other_host)
    monkeypatch.setattr(routers, "get_allowed_hosts", lambda: {allowed_host.lower()})
    netloc = f"[{other_host}]" if ":" in other_host else other_host
    url = f"{scheme}://{netloc}:{port}/cb"
    with pytest.raises(HTTPException):
        validate_callback_url(url)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(bad=st.sampled_from([" ", "\t", "\n", "\r", "\x00", "\x1f"]))
def test_rejects_netloc_with_bad_chars(monkeypatch, bad: str) -> None:
    """Spaces and control characters in netloc must be rejected."""
    monkeypatch.setattr(routers, "get_allowed_hosts", lambda: {"example.com"})
    url = f"http://example.com{bad}evil.com"
    with pytest.raises(HTTPException):
        validate_callback_url(url)
