"""Shared test fixtures for FactSynth API tests."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from factsynth_ultimate.app import app

API_KEY = os.getenv("API_KEY", "change-me")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def base_headers() -> dict[str, str]:
    return {"x-api-key": API_KEY, "content-type": "application/json"}


@pytest.fixture()
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

