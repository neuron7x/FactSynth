import time

import pytest
from fakeredis.aioredis import FakeRedis
from fastapi import FastAPI
from fastapi.testclient import TestClient

from factsynth_ultimate.core.ratelimit import RateLimitMiddleware


def _build_app(limit: int = 2, window: int = 1):
    redis = FakeRedis()
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        redis=redis,
        per_key=limit,
        per_ip=0,
        per_org=0,
        window=window,
    )

    @app.get("/route")
    async def route():
        return {"ok": True}

    return app, redis


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "k")


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_burst_limit_exceeded():
    app, _ = _build_app(limit=2, window=1)
    with TestClient(app) as client:
        headers = {"x-api-key": "k"}
        assert client.get("/route", headers=headers).status_code == 200
        assert client.get("/route", headers=headers).status_code == 200
        resp = client.get("/route", headers=headers)
        assert resp.status_code == 429
        assert resp.headers["X-RateLimit-Limit"] == "2"
        assert resp.headers["X-RateLimit-Remaining"] == "0"
        assert resp.headers["Retry-After"] == "1"
        assert "X-RateLimit-Reset" in resp.headers


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_limit_resets_after_window():
    app, _ = _build_app(limit=2, window=1)
    with TestClient(app) as client:
        headers = {"x-api-key": "k"}
        client.get("/route", headers=headers)
        client.get("/route", headers=headers)
        assert client.get("/route", headers=headers).status_code == 429
        time.sleep(1.1)
        resp = client.get("/route", headers=headers)
        assert resp.status_code == 200
        assert resp.headers["X-RateLimit-Remaining"] == "1"


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_headers_on_success():
    app, _ = _build_app(limit=2, window=1)
    with TestClient(app) as client:
        headers = {"x-api-key": "k"}
        resp = client.get("/route", headers=headers)
        assert resp.status_code == 200
        assert resp.headers["X-RateLimit-Limit"] == "2"
        assert resp.headers["X-RateLimit-Remaining"] == "1"
        assert resp.headers["X-RateLimit-Reset"] == "1"
