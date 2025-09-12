import os
from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app


def test_invalid_callback_scheme() -> None:
    env = {"API_KEY": "secret", "CALLBACK_URL_ALLOWED_HOSTS": "example.com"}
    with patch.dict(os.environ, env), TestClient(create_app()) as client:
        r = client.post(
            "/v1/score",
            headers={"x-api-key": "secret"},
            json={"text": "x", "callback_url": "ftp://example.com/cb"},
        )
        assert r.status_code == HTTPStatus.BAD_REQUEST
        assert r.json()["detail"] == "Invalid callback URL"


def test_invalid_callback_host() -> None:
    env = {"API_KEY": "secret", "CALLBACK_URL_ALLOWED_HOSTS": "example.com"}
    with patch.dict(os.environ, env), TestClient(create_app()) as client:
        r = client.post(
            "/v1/score",
            headers={"x-api-key": "secret"},
            json={"text": "x", "callback_url": "https://evil.com/cb"},
        )
        assert r.status_code == HTTPStatus.BAD_REQUEST
        assert r.json()["detail"] == "Invalid callback URL"


def test_valid_callback_url() -> None:
    env = {"API_KEY": "secret", "CALLBACK_URL_ALLOWED_HOSTS": "example.com"}
    with patch.dict(os.environ, env), TestClient(create_app()) as client:
        r = client.post(
            "/v1/score",
            headers={"x-api-key": "secret"},
            json={"text": "x", "callback_url": "https://example.com/cb"},
        )
        assert r.status_code == HTTPStatus.OK
        assert "score" in r.json()
