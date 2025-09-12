from http import HTTPStatus

import pytest


@pytest.mark.anyio
@pytest.mark.smoke
async def test_sse_stream_basic(client, base_headers):
    async with client.stream(
        "POST", "/v1/stream", headers=base_headers, json={"text": "stream this text"}
    ) as r:
        assert r.status_code == HTTPStatus.OK
        assert "text/event-stream" in r.headers.get("content-type", "")
        first = await r.aiter_bytes().__anext__()
        assert b"data:" in first or b"event:" in first
