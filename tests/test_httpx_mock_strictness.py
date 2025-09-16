import httpx
import pytest


def test_unexpected_http_request_fails(httpx_mock):
    httpx_mock.reset()
    with pytest.raises(httpx.TimeoutException, match="No response can be found"):
        httpx.get("https://example.com/")
    httpx_mock.reset()
