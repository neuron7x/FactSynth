import os
from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app
from factsynth_ultimate.core.ip_allowlist import IPAllowlistMiddleware


def test_forbidden_ip_returns_403():
    with patch.dict(os.environ, {"API_KEY": "secret"}):
        app = create_app()
        app.add_middleware(IPAllowlistMiddleware, cidrs=["127.0.0.1/32"])
        with TestClient(app) as client:
            r = client.post("/v1/score", headers={"x-api-key": "secret"}, json={"text": "x"})
            assert r.status_code == HTTPStatus.FORBIDDEN
            body = r.json()
            for field in ("type", "title", "status", "detail", "trace_id"):
                assert field in body
