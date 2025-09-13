import pytest
from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app


pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_api_key_allow_list(monkeypatch):
    monkeypatch.setenv("ALLOWED_API_KEYS", '["a","b"]')
    monkeypatch.setenv("RATE_LIMIT_REDIS_URL", "memory://")
    app = create_app()
    with TestClient(app) as client:
        headers = {"x-api-key": "a"}
        resp = client.post("/v1/generate", json={"text": "hi"}, headers=headers)
        assert resp.status_code == 200
        resp = client.post("/v1/generate", json={"text": "hi"}, headers={"x-api-key": "c"})
        assert resp.status_code == 403
