import asyncio
from http import HTTPStatus

import pytest

from factsynth_ultimate.api import routers
from factsynth_ultimate.core.metrics import current_sse_tokens
from factsynth_ultimate.schemas.requests import ScoreReq

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


@pytest.mark.anyio
async def test_sse_stream_stops_on_disconnect(monkeypatch):
    class DummyRequest:
        def __init__(self) -> None:
            self.calls = 0

        async def is_disconnected(self) -> bool:
            self.calls += 1
            return self.calls > 2  # noqa: PLR2004

    class DummyRetriever:
        def __init__(self) -> None:
            self.closed = False

        async def aclose(self) -> None:
            self.closed = True

    retr = DummyRetriever()

    class DummyTokens(list):
        def __init__(self) -> None:
            super().__init__(["a", "b", "c"])
            self.retriever = retr

    def fake_tokenize_preview(text: str, max_tokens: int = 256) -> DummyTokens:
        del text, max_tokens
        return DummyTokens()

    monkeypatch.setattr(routers, "tokenize_preview", fake_tokenize_preview)

    initial = current_sse_tokens()
    resp = await routers.stream(ScoreReq(text="whatever"), DummyRequest())
    agen = resp.body_iterator
    parts: list[str] = []
    while True:
        try:
            part = await agen.__anext__()
            parts.append(part)
            await asyncio.sleep(0.01)
        except StopAsyncIteration:
            break

    assert retr.closed
    diff = current_sse_tokens() - initial
    assert diff == 2  # noqa: PLR2004
    assert any("event: end" in p for p in parts)
