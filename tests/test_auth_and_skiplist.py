from http import HTTPStatus

import pytest


@pytest.mark.anyio
async def test_generate_requires_api_key(client):
    r = await client.post("/v1/generate", json={"text": "hello"})
    assert r.status_code in (401, 403)


@pytest.mark.anyio
async def test_metrics_and_health_are_public(client):
    r1 = await client.get("/metrics")
    r2 = await client.get("/v1/healthz")
    assert r1.status_code == HTTPStatus.OK
    assert r2.status_code == HTTPStatus.OK
