from http import HTTPStatus

import pytest


pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


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


@pytest.mark.anyio
async def test_sse_stream_custom_token_delay(client, base_headers, monkeypatch):
    calls: list[float] = []

    async def fake_sleep(value: float) -> None:  # pragma: no cover - behavior verified via calls
        calls.append(value)

    monkeypatch.setattr("factsynth_ultimate.api.routers.asyncio.sleep", fake_sleep)
    async with client.stream(
        "POST",
        "/v1/stream?token_delay=0.01",
        headers=base_headers,
        json={"text": "delayed"},
    ) as r:
        assert r.status_code == HTTPStatus.OK
        await r.aread()

    assert calls and all(call == pytest.approx(0.01) for call in calls)
