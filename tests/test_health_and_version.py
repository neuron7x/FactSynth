from http import HTTPStatus

import pytest


@pytest.mark.anyio
async def test_healthz(client):
    r = await client.get("/v1/healthz")
    assert r.status_code == HTTPStatus.OK
    assert r.headers["content-type"].startswith("application/json")


@pytest.mark.anyio
async def test_version(client, base_headers):
    r = await client.get("/v1/version", headers=base_headers)
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert "version" in data and isinstance(data["version"], str)

