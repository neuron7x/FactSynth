import importlib

import pytest
from httpx import ASGITransport, AsyncClient

from factsynth_ultimate.infra.db import init_db


@pytest.mark.asyncio
async def test_create_and_verify_flow() -> None:
    mod = importlib.import_module("factsynth_ultimate.app")
    app = mod.app
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/claims", json={"text": "The sky is blue"})
        assert r.status_code == 200  # noqa: S101
        cid = r.json()["id"]
        rv = await ac.post(f"/claims/{cid}/verify")
        assert rv.status_code == 200  # noqa: S101
        assert rv.json()["id"] == cid  # noqa: S101
