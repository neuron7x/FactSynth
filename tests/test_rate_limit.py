"""Integration tests for the custom rate limiting middleware."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import FastAPI
from fastapi.testclient import TestClient

from factsynth_ultimate.core.rate_limit import RateLimitMiddleware, RateQuota
from factsynth_ultimate.store.memory import MemoryStore


def _build_app(
    *,
    api_quota: RateQuota = RateQuota(2, 1.0),
    ip_quota: RateQuota | None = None,
    org_quota: RateQuota | None = None,
) -> FastAPI:
    """Create a FastAPI app with an in-memory rate limiter for testing."""

    store = MemoryStore()
    app = FastAPI()

    app.add_middleware(
        RateLimitMiddleware,
        redis=store,  # type: ignore[arg-type]
        memory_store=store,
        api=api_quota,
        ip=ip_quota or RateQuota(0, 1.0),
        org=org_quota or RateQuota(0, 1.0),
        key_header="x-api-key",
    )

    @app.get("/route")
    async def route() -> dict[str, bool]:
        return {"ok": True}

    return app


def test_burst_limit_exceeded() -> None:
    app = _build_app()
    with TestClient(app) as client:
        headers = {"x-api-key": "k"}
        assert client.get("/route", headers=headers).status_code == HTTPStatus.OK
        assert client.get("/route", headers=headers).status_code == HTTPStatus.OK
        resp = client.get("/route", headers=headers)
        assert resp.status_code == HTTPStatus.TOO_MANY_REQUESTS
        assert resp.headers["X-RateLimit-Limit"] == "2"
        assert resp.headers["X-RateLimit-Remaining"] == "0"
        assert resp.headers["Retry-After"] == "1"


def test_limit_resets_after_window(time_travel) -> None:
    app = _build_app()
    with TestClient(app) as client:
        headers = {"x-api-key": "k"}
        client.get("/route", headers=headers)
        client.get("/route", headers=headers)
        assert client.get("/route", headers=headers).status_code == HTTPStatus.TOO_MANY_REQUESTS
        time_travel.shift(1.1)
        resp = client.get("/route", headers=headers)
        assert resp.status_code == HTTPStatus.OK
        assert resp.headers["X-RateLimit-Remaining"] == "0"


def test_headers_on_success() -> None:
    app = _build_app()
    with TestClient(app) as client:
        headers = {"x-api-key": "k"}
        resp = client.get("/route", headers=headers)
        assert resp.status_code == HTTPStatus.OK
        assert resp.headers["X-RateLimit-Limit"] == "2"
        assert resp.headers["X-RateLimit-Remaining"] == "1"


def test_missing_api_key_not_rate_limited() -> None:
    app = _build_app()
    with TestClient(app) as client:
        assert client.get("/route").status_code == HTTPStatus.OK
        assert client.get("/route").status_code == HTTPStatus.OK
        # The limiter ignores requests without an API key.
        assert client.get("/route").status_code == HTTPStatus.OK
