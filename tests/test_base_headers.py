import pytest


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_base_headers_uses_latest_api_key(monkeypatch, request):
    monkeypatch.setenv("API_KEY", "patched-key")

    headers = request.getfixturevalue("base_headers")

    assert headers["x-api-key"] == "patched-key"
    assert headers["content-type"] == "application/json"
