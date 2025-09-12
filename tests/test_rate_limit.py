import importlib
import os
import time
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient
from fakeredis.aioredis import FakeRedis

from factsynth_ultimate.app import create_app
from factsynth_ultimate.core import settings as settings_module


def _build_app(per_key=1, per_ip=100, per_org=100, window=60):
    fake = FakeRedis()
    env = {
        "API_KEY": "secret",
        "RATE_LIMIT_REDIS_URL": "redis://test",
        "RATE_LIMIT_PER_KEY": str(per_key),
        "RATE_LIMIT_PER_IP": str(per_ip),
        "RATE_LIMIT_PER_ORG": str(per_org),
    }
    with patch.dict(os.environ, env, clear=True):
        importlib.reload(settings_module)
        with patch("redis.asyncio.from_url", return_value=fake):
            app = create_app(rate_limit_window=window)
    return app, fake


def test_rate_limit_exceeded_returns_429():
    app, _ = _build_app(per_key=1)
    with TestClient(app) as client:
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


def test_rate_limit_resets_after_window():
    app, _ = _build_app(per_key=1, window=1)
    with TestClient(app) as client:
        headers = {"x-api-key": "secret"}
        assert client.post("/v1/score", headers=headers, json={"text": "x"}).status_code == HTTPStatus.OK
        assert client.post("/v1/score", headers=headers, json={"text": "x"}).status_code == HTTPStatus.TOO_MANY_REQUESTS
        time.sleep(1.1)
        assert client.post("/v1/score", headers=headers, json={"text": "x"}).status_code == HTTPStatus.OK


def test_rate_limit_concurrency_safety():
    app, _ = _build_app(per_key=1)
    with TestClient(app) as client:
        headers = {"x-api-key": "secret"}

        def _request():
            return client.post("/v1/score", headers=headers, json={"text": "x"}).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: _request(), range(2)))
        assert sorted(results) == [HTTPStatus.OK, HTTPStatus.TOO_MANY_REQUESTS]
