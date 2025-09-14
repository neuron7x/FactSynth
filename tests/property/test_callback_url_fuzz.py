import os
import string
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from factsynth_ultimate.api.routers import reload_allowed_hosts, validate_callback_url

try:  # pragma: no cover - optional import
    from hypothesis import given
    from hypothesis import strategies as st
except ModuleNotFoundError:  # pragma: no cover - optional
    pytest.skip("hypothesis not installed", allow_module_level=True)

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)

ALLOWED_HOSTS = ["example.com", "домен.укр", "::1"]


def _build_url(scheme: str, host: str, port: int, path: str) -> str:
    host_part = host
    if ":" in host and not host.startswith("["):
        host_part = f"[{host}]"
    return f"{scheme}://{host_part}:{port}/{path}"


@given(
    scheme=st.sampled_from(["http", "https"]),
    host=st.sampled_from(ALLOWED_HOSTS),
    port=st.integers(min_value=1, max_value=65535),
    path=st.text(alphabet=string.ascii_letters + string.digits + "/-_.", min_size=0, max_size=20),
)
def test_validate_callback_url_allows_allowed_hosts(
    scheme: str, host: str, port: int, path: str
) -> None:
    url = _build_url(scheme, host, port, path)
    env = {"CALLBACK_URL_ALLOWED_HOSTS": ",".join(ALLOWED_HOSTS)}
    with patch.dict(os.environ, env):
        reload_allowed_hosts()
        validate_callback_url(url)


@given(
    scheme=st.sampled_from(["http", "https"]),
    host=st.one_of(
        st.ip_addresses().map(str),
        st.from_regex(r"[a-z]{1,10}\.[a-z]{2,3}", fullmatch=True),
    ).filter(lambda h: h not in ALLOWED_HOSTS),
    port=st.integers(min_value=1, max_value=65535),
    path=st.text(alphabet=string.ascii_letters + string.digits + "/-_.", min_size=0, max_size=20),
)
def test_validate_callback_url_rejects_disallowed_host(
    scheme: str, host: str, port: int, path: str
) -> None:
    url = _build_url(scheme, host, port, path)
    env = {"CALLBACK_URL_ALLOWED_HOSTS": ",".join(ALLOWED_HOSTS)}
    with patch.dict(os.environ, env):
        reload_allowed_hosts()
        with pytest.raises(HTTPException):
            validate_callback_url(url)


@given(
    scheme=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=10).filter(
        lambda s: s not in {"http", "https"}
    ),
    host=st.sampled_from(ALLOWED_HOSTS),
    port=st.integers(min_value=1, max_value=65535),
    path=st.text(alphabet=string.ascii_letters + string.digits + "/-_.", min_size=0, max_size=20),
)
def test_validate_callback_url_rejects_scheme(
    scheme: str, host: str, port: int, path: str
) -> None:
    url = _build_url(scheme, host, port, path)
    env = {"CALLBACK_URL_ALLOWED_HOSTS": ",".join(ALLOWED_HOSTS)}
    with patch.dict(os.environ, env):
        reload_allowed_hosts()
        with pytest.raises(HTTPException):
            validate_callback_url(url)


@pytest.mark.parametrize(
    "netloc",
    [
        "exa mple.com",
        "example.com ",
        "exam\x00ple.com",
    ],
)
def test_validate_callback_url_bad_netloc(netloc: str) -> None:
    url = f"https://{netloc}/"
    env = {"CALLBACK_URL_ALLOWED_HOSTS": "example.com"}
    with patch.dict(os.environ, env):
        reload_allowed_hosts()
        with pytest.raises(HTTPException):
            validate_callback_url(url)
