import importlib
import os
from http import HTTPStatus
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app
from factsynth_ultimate.core import settings as settings_module
from factsynth_ultimate.core.ip_allowlist import IPAllowlistMiddleware

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_forbidden_ip_returns_403(httpx_mock):
    httpx_mock.reset(assert_all_responses_were_requested=False)
    env = {"API_KEY": "secret", "IP_ALLOWLIST": '["127.0.0.2/32"]'}
    with patch.dict(os.environ, env):
        importlib.reload(settings_module)
        with TestClient(create_app()) as client:
            r = client.post("/v1/score", headers={"x-api-key": "secret"}, json={"text": "x"})
            assert r.status_code == HTTPStatus.FORBIDDEN
            body = r.json()
            trace_id = body.pop("trace_id")
            assert trace_id
            assert body == {
                "type": "about:blank",
                "title": "Forbidden",
                "status": HTTPStatus.FORBIDDEN,
                "detail": "IP testclient not allowed",
            }


def test_empty_allowlist_blocks_request(httpx_mock):
    httpx_mock.reset(assert_all_responses_were_requested=False)
    app = FastAPI()
    app.add_middleware(IPAllowlistMiddleware, cidrs=[])

    @app.get("/")
    def root() -> dict[str, str]:  # pragma: no cover - trivial
        return {"status": "ok"}

    with TestClient(app) as client:
        r = client.get("/")
        assert r.status_code == HTTPStatus.FORBIDDEN
