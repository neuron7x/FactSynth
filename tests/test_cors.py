import importlib
import os
from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app
from factsynth_ultimate.core import settings as settings_module


def test_disallowed_origin_rejected():
    env = {"API_KEY": "secret", "CORS_ALLOWED_ORIGINS": '["https://allowed.com"]'}
    with patch.dict(os.environ, env, clear=True):
        importlib.reload(settings_module)
        with TestClient(create_app()) as client:
            r = client.options(
                "/v1/healthz",
                headers={
                    "Origin": "https://evil.com",
                    "Access-Control-Request-Method": "GET",
                },
            )
            assert r.status_code == HTTPStatus.BAD_REQUEST
