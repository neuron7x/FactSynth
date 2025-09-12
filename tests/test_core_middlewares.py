from http import HTTPStatus

from fastapi import FastAPI
from fastapi.testclient import TestClient

from factsynth_ultimate.core.body_limit import BodySizeLimitMiddleware
from factsynth_ultimate.core.security_headers import SecurityHeadersMiddleware


def _make_app():
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=10)
    app.add_middleware(SecurityHeadersMiddleware, hsts=True)

    @app.post("/")
    async def root(data: dict):
        return data

    @app.get("/")
    async def get_root():
        return {"ok": True}

    return app


def test_body_size_limit_triggers_413():
    app = _make_app()
    client = TestClient(app)
    big = {"k": "x" * 20}
    r = client.post("/", json=big)
    assert r.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    body = r.json()
    assert body["status"] == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    assert "exceeds limit" in body["detail"]


def test_security_headers_added():
    app = _make_app()
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == HTTPStatus.OK
    headers = r.headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Content-Security-Policy"].startswith("default-src")
    assert headers["Strict-Transport-Security"].startswith("max-age")
