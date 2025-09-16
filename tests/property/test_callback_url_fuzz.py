import os
import string
from http import HTTPStatus
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from factsynth_ultimate.api.routers import (
    get_allowed_hosts,
    reload_allowed_hosts,
    validate_callback_url,
)

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
        allowed = get_allowed_hosts()
        problem = validate_callback_url(url, allowed)
        assert problem is None

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
        allowed = get_allowed_hosts()
        problem = validate_callback_url(url, allowed)
        assert problem is not None
        assert problem.status == HTTPStatus.BAD_REQUEST
        assert problem.extras and problem.extras.get("reason") == "host_not_allowed"

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
        allowed = get_allowed_hosts()
        problem = validate_callback_url(url, allowed)
        assert problem is not None
        assert problem.status == HTTPStatus.BAD_REQUEST
        assert problem.extras and problem.extras.get("reason") == "scheme_not_allowed"

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
        allowed = get_allowed_hosts()
        problem = validate_callback_url(url, allowed)
        assert problem is not None
        assert problem.status == HTTPStatus.BAD_REQUEST
        assert problem.extras and problem.extras.get("reason") == "host_not_allowed"
