import time

import pytest
from fakeredis.aioredis import FakeRedis
from fastapi import FastAPI
from fastapi.testclient import TestClient

from factsynth_ultimate.core.rate_limit import RateLimitMiddleware


def _build_app(burst=2, sustain=1.0):
    redis = FakeRedis()
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, redis=redis, burst=burst, sustain=sustain)

    @app.get("/route")
    async def route():
        return {"ok": True}

    return app, redis


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_burst_limit_exceeded():
    app, _ = _build_app(burst=2, sustain=1)
    with TestClient(app) as client:
        headers = {"x-api-key": "k"}
        assert client.get("/route", headers=headers).status_code == 200
        assert client.get("/route", headers=headers).status_code == 200
        resp = client.get("/route", headers=headers)
        assert resp.status_code == 429
        assert resp.headers["X-RateLimit-Limit"] == "2"
        assert resp.headers["X-RateLimit-Remaining"] == "0"
        assert resp.headers["Retry-After"] == "1"


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_sustained_requests_allowed():
    app, _ = _build_app(burst=2, sustain=4)
    with TestClient(app) as client:
        headers = {"x-api-key": "k"}
        for _ in range(5):
            resp = client.get("/route", headers=headers)
            assert resp.status_code == 200
            time.sleep(0.3)
