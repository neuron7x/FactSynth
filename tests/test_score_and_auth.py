import os
from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app


def test_auth_required() -> None:
    with patch.dict(os.environ, {"API_KEY": "secret"}), TestClient(
        create_app()
    ) as client:
        url = "/v1/score"
        assert client.post(url, json={"text": "x"}).status_code == HTTPStatus.UNAUTHORIZED
        assert (
            client.post(url, headers={"x-api-key": "secret"}, json={"text": "x"}).status_code
            == HTTPStatus.OK
        )


def test_score_values() -> None:
    with patch.dict(os.environ, {"API_KEY": "secret"}), TestClient(
        create_app()
    ) as client:
        r = client.post(
            "/v1/score",
            headers={"x-api-key": "secret"},
            json={"text": "hello world", "targets": ["hello", "x"]},
        )
        assert r.status_code == HTTPStatus.OK
        s = r.json()["score"]
        assert 0.0 <= s <= 1.0
