import importlib
import os
from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app
from factsynth_ultimate.core import settings as settings_module


def test_forbidden_ip_returns_403():
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
