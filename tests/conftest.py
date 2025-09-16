"""Shared test fixtures for FactSynth API tests."""

import asyncio
import json
import os
import random
import string

import fakeredis
import pytest
import time_machine
from httpx import ASGITransport, AsyncClient, MockTransport, Response

os.environ.setdefault("RATE_LIMIT_REDIS_URL", "memory://")
os.environ.setdefault("RATE_LIMIT_PER_KEY", "1000")
os.environ.setdefault("RATE_LIMIT_PER_IP", "1000")
os.environ.setdefault("RATE_LIMIT_PER_ORG", "1000")
os.environ.setdefault("RATES_API", '{"burst": 1000, "sustain": 1.0}')
os.environ.setdefault("RATES_IP", '{"burst": 1000, "sustain": 1.0}')
os.environ.setdefault("RATES_ORG", '{"burst": 1000, "sustain": 1.0}')

from factsynth_ultimate.app import create_app

# Ensure a default event loop for tests that rely on get_event_loop()
asyncio.set_event_loop(asyncio.new_event_loop())

# Provide a backwards-compatible get_event_loop for tests
_orig_get_event_loop = asyncio.get_event_loop


def _get_event_loop():
    try:
        return _orig_get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


asyncio.get_event_loop = _get_event_loop


def stub_handler(request):
    path = request.url.path

    if path.endswith("/v1/generate"):
        content = request.content or b""
        if isinstance(content, bytes):
            content = content.decode()
        payload = json.loads(content or "{}")
        text = payload.get("text", "")
        seed = payload.get("seed", 0)
        rng = random.Random(seed)
        alphabet = string.ascii_letters + string.digits + " "
        out = "".join(rng.choice(alphabet) for _ in text)
        return Response(200, json={"output": {"text": out}})

    if path.endswith("/v1/score"):
        return Response(200, json={"score": 0.0})

    if path.endswith("/openapi.json"):
        return Response(
            200,
            json={
                "openapi": "3.1.0",
                "info": {"title": "stub", "version": "0.1.0"},
                "paths": {"/v1/score": {"post": {"responses": {"200": {"description": "OK"}}}}},
            },
        )

    return Response(200, json={"stub": True})


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture()
def base_headers() -> dict[str, str]:
    api_key = os.getenv("API_KEY", "change-me")
    return {"x-api-key": api_key, "content-type": "application/json"}


@pytest.fixture()
def assert_all_responses_were_requested() -> bool:
    """Disable strict assertion on httpx mocks by default."""

    return False


@pytest.fixture()
def time_travel():
    """Provide a controllable clock for tests."""

    with time_machine.travel(0, tick=False) as traveler:
        yield traveler


@pytest.fixture()
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
async def api_stub():
    """Async client that returns deterministic responses for external APIs."""

    transport = MockTransport(stub_handler)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def _stub_external_api(httpx_mock) -> None:
    """Stub external HTTP calls so tests remain offline."""

    httpx_mock.add_callback(stub_handler)


@pytest.fixture(autouse=True)
def _reset_fake_redis() -> None:
    client = fakeredis.FakeRedis()
    client.flushall()
    try:
        yield
    finally:
        client.flushall()
