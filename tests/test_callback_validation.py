import os
from http import HTTPStatus
from http import HTTPStatus
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app


pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_invalid_callback_scheme() -> None:
    env = {"API_KEY": "secret", "CALLBACK_URL_ALLOWED_HOSTS": "example.com"}
    with patch.dict(os.environ, env), TestClient(create_app()) as client:
        response = client.post(
            "/v1/score",
            headers={"x-api-key": "secret"},
            json={"text": "x", "callback_url": "ftp://example.com/cb"},
        )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == HTTPStatus.BAD_REQUEST
    assert "scheme" in body["detail"].lower()


def test_invalid_callback_host() -> None:
    env = {"API_KEY": "secret", "CALLBACK_URL_ALLOWED_HOSTS": "example.com"}
    with patch.dict(os.environ, env), TestClient(create_app()) as client:
        response = client.post(
            "/v1/score",
            headers={"x-api-key": "secret"},
            json={"text": "x", "callback_url": "https://evil.com/cb"},
        )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    body = response.json()
    assert "evil.com" in body["detail"]
    assert "example.com" in body["detail"]


def test_valid_callback_url() -> None:
    env = {"API_KEY": "secret", "CALLBACK_URL_ALLOWED_HOSTS": "example.com"}
    with patch.dict(os.environ, env), TestClient(create_app()) as client:
        response = client.post(
            "/v1/score",
            headers={"x-api-key": "secret"},
            json={"text": "x", "callback_url": "https://example.com/cb"},
        )
    assert response.status_code == HTTPStatus.OK
    assert "score" in response.json()
