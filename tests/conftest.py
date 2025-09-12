"""Shared test fixtures for FactSynth API tests."""

import asyncio
import json
import os
import random
import string
from unittest.mock import patch

import pytest
from fakeredis.aioredis import FakeRedis
from httpx import ASGITransport, AsyncClient, MockTransport, Response

# Global Redis patch so tests don't require a real server
_FAKE_REDIS = FakeRedis()
patch("redis.asyncio.from_url", return_value=_FAKE_REDIS).start()
os.environ.setdefault("RATE_LIMIT_REDIS_URL", "redis://test")
os.environ.setdefault("RATE_LIMIT_PER_KEY", "1000")
os.environ.setdefault("RATE_LIMIT_PER_IP", "1000")
os.environ.setdefault("RATE_LIMIT_PER_ORG", "1000")

from factsynth_ultimate.app import create_app  # noqa: E402

API_KEY = os.getenv("API_KEY", "change-me")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def base_headers() -> dict[str, str]:
    return {"x-api-key": API_KEY, "content-type": "application/json"}


@pytest.fixture()
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
async def api_stub():
    """Async client that returns deterministic responses for external APIs."""

    def handler(request):
        path = request.url.path
        if path == "/v1/generate":
            payload = json.loads(request.content.decode() or "{}")
            text = payload.get("text", "")
            seed = payload.get("seed", 0)
            rng = random.Random(seed)
            alphabet = string.ascii_letters + string.digits + " "
            out = "".join(rng.choice(alphabet) for _ in text)
            return Response(200, json={"output": {"text": out}})
        if path == "/v1/score":
            return Response(200, json={"score": 0.0})
        if path == "/openapi.json":
            return Response(
                200,
                json={
                    "openapi": "3.1.0",
                    "info": {"title": "stub", "version": "0.1.0"},
                    "paths": {
                        "/v1/score": {"post": {"responses": {"200": {"description": "OK"}}}}
                    },
                },
            )
        return Response(404)

    transport = MockTransport(handler)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def _stub_external_api(monkeypatch) -> None:
    """Stub external HTTP calls so tests remain offline."""

    original_post = AsyncClient.post
    original_get = AsyncClient.get

    async def _fake_post(self, url, *args, **kwargs):
        if getattr(self, "_transport", None) is not None:
            return await original_post(self, url, *args, **kwargs)
        url_str = str(url)
        if url_str.endswith("/v1/generate"):
            return Response(200, json={"output": {"text": "stub"}})
        if url_str.endswith("/v1/score"):
            return Response(200, json={"score": 0.0})
        return Response(200, json={"stub": True})

    async def _fake_get(self, url, *args, **kwargs):
        if getattr(self, "_transport", None) is not None:
            return await original_get(self, url, *args, **kwargs)
        url_str = str(url)
        if url_str.endswith("/openapi.json"):
            return Response(200, json={"openapi": "3.1.0", "paths": {}})
        return Response(200, json={"stub": True})

    monkeypatch.setattr(AsyncClient, "post", _fake_post)
    monkeypatch.setattr(AsyncClient, "get", _fake_get)


@pytest.fixture(autouse=True)
def _reset_fake_redis() -> None:
    asyncio.run(_FAKE_REDIS.flushall())
