import time
from http import HTTPStatus

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from factsynth_ultimate.core.auth import APIKeyAuthMiddleware

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
        assert client.get("/route", headers=headers).status_code == HTTPStatus.OK
        assert client.get("/route", headers=headers).status_code == HTTPStatus.OK
        resp = client.get("/route", headers=headers)
        assert resp.status_code == HTTPStatus.TOO_MANY_REQUESTS
        assert resp.headers["X-RateLimit-Limit"] == "2"
        assert resp.headers["X-RateLimit-Remaining"] == "0"
        assert "Retry-After" in resp.headers


def test_limit_resets_after_window():
    app = _build_app()
    with TestClient(app) as client:
        headers = {"x-api-key": "k"}
        client.get("/route", headers=headers)
        client.get("/route", headers=headers)
        assert client.get("/route", headers=headers).status_code == HTTPStatus.TOO_MANY_REQUESTS
        time.sleep(1.1)
        resp = client.get("/route", headers=headers)
        assert resp.status_code == HTTPStatus.OK
        assert resp.headers["X-RateLimit-Remaining"] == "1"


def test_headers_on_success():
    app = _build_app()
    with TestClient(app) as client:
        headers = {"x-api-key": "k"}
        resp = client.get("/route", headers=headers)
        assert resp.status_code == HTTPStatus.OK
        assert resp.headers["X-RateLimit-Limit"] == "2"
        assert resp.headers["X-RateLimit-Remaining"] == "1"


def test_unauthorized_requests_are_rate_limited():
    app = FastAPI()
    limiter = Limiter(
        key_func=lambda request: request.headers.get("x-api-key")
        or request.client.host,
        default_limits=["2/1 second"],
        storage_uri="memory://",
        headers_enabled=True,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.get("/route")
    async def route():
        return {"ok": True}

    app.add_middleware(
        APIKeyAuthMiddleware,
        api_keys={"valid"},
        header_name="x-api-key",
        skip=(),
    )
    app.add_middleware(SlowAPIMiddleware)

    with TestClient(app) as client:
        assert client.get("/route").status_code == HTTPStatus.UNAUTHORIZED
        assert client.get("/route").status_code == HTTPStatus.UNAUTHORIZED
        resp = client.get("/route")
        assert resp.status_code == HTTPStatus.TOO_MANY_REQUESTS
        assert resp.headers["X-RateLimit-Limit"] == "2"
        assert resp.headers["X-RateLimit-Remaining"] == "0"
