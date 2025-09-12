from fastapi import FastAPI
from fastapi.testclient import TestClient

from factsynth_ultimate.core.security_headers import SecurityHeadersMiddleware


def test_security_headers_default_and_hsts() -> None:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, hsts=True)

    @app.get("/")
    def root():
        return {"ok": True}

    with TestClient(app) as client:
        r = client.get("/")
        assert r.headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" in r.headers


def test_security_headers_custom() -> None:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, headers={"X-Test": "1"})

    @app.get("/")
    def root():
        return {"ok": True}

    with TestClient(app) as client:
        r = client.get("/")
        assert r.headers["X-Test"] == "1"
        assert r.headers["X-Content-Type-Options"] == "nosniff"
