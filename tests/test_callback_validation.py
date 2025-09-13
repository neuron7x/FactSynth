import importlib
import os
from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient

import factsynth_ultimate.app as app_module
from factsynth_ultimate.api import routers


def test_invalid_callback_scheme(httpx_mock) -> None:
    httpx_mock.reset()
    env = {"API_KEY": "secret", "CALLBACK_URL_ALLOWED_HOSTS": "example.com"}
    with patch.dict(os.environ, env):
        importlib.reload(routers)
        importlib.reload(app_module)
        with TestClient(app_module.create_app()) as client:
            r = client.post(
                "/v1/score",
                headers={"x-api-key": "secret"},
                json={"text": "x", "callback_url": "ftp://example.com/cb"},
            )
            assert r.status_code == HTTPStatus.BAD_REQUEST
            assert r.json()["detail"] == "Invalid callback URL"


def test_invalid_callback_host(httpx_mock) -> None:
    httpx_mock.reset()
    env = {"API_KEY": "secret", "CALLBACK_URL_ALLOWED_HOSTS": "example.com"}
    with patch.dict(os.environ, env):
        importlib.reload(routers)
        importlib.reload(app_module)
        with TestClient(app_module.create_app()) as client:
            r = client.post(
                "/v1/score",
                headers={"x-api-key": "secret"},
                json={"text": "x", "callback_url": "https://evil.com/cb"},
            )
            assert r.status_code == HTTPStatus.BAD_REQUEST
            assert r.json()["detail"] == "Invalid callback URL"


def test_valid_callback_url(httpx_mock) -> None:
    httpx_mock.reset()
    httpx_mock.add_response(url="https://example.com/cb", status_code=200)
    env = {"API_KEY": "secret", "CALLBACK_URL_ALLOWED_HOSTS": "example.com"}
    with patch.dict(os.environ, env):
        importlib.reload(routers)
        importlib.reload(app_module)
        with TestClient(app_module.create_app()) as client:
            r = client.post(
                "/v1/score",
                headers={"x-api-key": "secret"},
                json={"text": "x", "callback_url": "https://example.com/cb"},
            )
            assert r.status_code == HTTPStatus.OK
            assert "score" in r.json()
