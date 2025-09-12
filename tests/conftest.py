"""Shared test fixtures for FactSynth API tests."""

import asyncio
import os
from unittest.mock import patch

import pytest
from fakeredis.aioredis import FakeRedis
from httpx import ASGITransport, AsyncClient, Response

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


@pytest.fixture(autouse=True)
def _stub_external_post(monkeypatch) -> None:
    original_post = AsyncClient.post

    async def _fake_post(self, url, *args, **kwargs):
        if getattr(self, "_transport", None) is not None:
            return await original_post(self, url, *args, **kwargs)
        return Response(200, json={"stub": True})

    monkeypatch.setattr(AsyncClient, "post", _fake_post)


@pytest.fixture(autouse=True)
def _reset_fake_redis() -> None:
    asyncio.run(_FAKE_REDIS.flushall())
