import importlib
import os
from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app
from factsynth_ultimate.core import settings as settings_module


def test_rate_limit_exceeded_returns_429():
    with patch.dict(os.environ, {"API_KEY": "secret", "RATE_LIMIT_PER_MINUTE": "1"}):
        importlib.reload(settings_module)
        with TestClient(create_app()) as client:
            headers = {"x-api-key": "secret"}
            assert client.post("/v1/score", headers=headers, json={"text": "x"}).status_code == HTTPStatus.OK
            r = client.post("/v1/score", headers=headers, json={"text": "x"})
            assert r.status_code == HTTPStatus.TOO_MANY_REQUESTS
            body = r.json()
            trace_id = body.pop("trace_id")
            assert trace_id
            assert body == {
                "type": "about:blank",
                "title": "Too Many Requests",
                "status": HTTPStatus.TOO_MANY_REQUESTS,
                "detail": "Request rate limit exceeded",
            }


def test_rate_limit_localized_messages():
    with patch.dict(os.environ, {"API_KEY": "secret", "RATE_LIMIT_PER_MINUTE": "1"}):
        importlib.reload(settings_module)
        for lang, title in [("en", "Too Many Requests"), ("uk", "Забагато запитів")]:
            with TestClient(create_app()) as client:
                headers = {"x-api-key": "secret"}
                client.post("/v1/score", headers=headers, json={"text": "x"})
                r = client.post(
                    "/v1/score",
                    headers={"x-api-key": "secret", "accept-language": lang},
                    json={"text": "x"},
                )
                assert r.status_code == HTTPStatus.TOO_MANY_REQUESTS
                body = r.json()
                trace_id = body.pop("trace_id")
                assert trace_id
                assert body == {
                    "type": "about:blank",
                    "title": title,
                    "status": HTTPStatus.TOO_MANY_REQUESTS,
                    "detail": "Request rate limit exceeded",
                }
