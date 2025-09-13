import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware


pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def _build_app(limit: str = "2/1 second") -> FastAPI:
    app = FastAPI()
    limiter = Limiter(
        key_func=lambda request: request.headers.get("x-api-key", ""),
        default_limits=[limit],
        storage_uri="memory://",
        headers_enabled=True,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.get("/route")
    async def route():
        return {"ok": True}

    return app


def test_burst_limit_exceeded():
    app = _build_app()
    with TestClient(app) as client:
        headers = {"x-api-key": "k"}
        assert client.get("/route", headers=headers).status_code == 200
        assert client.get("/route", headers=headers).status_code == 200
        resp = client.get("/route", headers=headers)
        assert resp.status_code == 429
        assert resp.headers["X-RateLimit-Limit"] == "2"
        assert resp.headers["X-RateLimit-Remaining"] == "0"
        assert "Retry-After" in resp.headers


def test_limit_resets_after_window():
    app = _build_app()
    with TestClient(app) as client:
        headers = {"x-api-key": "k"}
        client.get("/route", headers=headers)
        client.get("/route", headers=headers)
        assert client.get("/route", headers=headers).status_code == 429
        time.sleep(1.1)
        resp = client.get("/route", headers=headers)
        assert resp.status_code == 200
        assert resp.headers["X-RateLimit-Remaining"] == "1"


def test_headers_on_success():
    app = _build_app()
    with TestClient(app) as client:
        headers = {"x-api-key": "k"}
        resp = client.get("/route", headers=headers)
        assert resp.status_code == 200
        assert resp.headers["X-RateLimit-Limit"] == "2"
        assert resp.headers["X-RateLimit-Remaining"] == "1"
