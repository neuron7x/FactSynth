import asyncio

import pytest
from fastapi.testclient import TestClient

from factsynth_ultimate.api import routers
from factsynth_ultimate.app import create_app
from factsynth_ultimate.core.metrics import current_sse_tokens
from factsynth_ultimate.schemas.requests import ScoreReq

TOTAL_TOKENS = 100
MAX_TOKENS = 256


def test_stream_sse_client_disconnect() -> None:
    text = " ".join(str(i) for i in range(TOTAL_TOKENS))
    initial = current_sse_tokens()
    with (
        TestClient(create_app()) as client,
        client.stream(
            "POST",
            "/v1/stream",
            headers={"x-api-key": "change-me"},
            json={"text": text},
        ),
    ):
        # Do not consume the stream to simulate client disconnect.
        pass
    diff = current_sse_tokens() - initial
    assert diff <= TOTAL_TOKENS


def test_stream_sse_client_cancel(monkeypatch) -> None:
    class DummyRequest:
        async def is_disconnected(self) -> bool:
            return False

    class DummyTokenizer:
        def __init__(self, tokens: list[str]):
            self._tokens = tokens
            self.closed = False

        def __iter__(self):
            return iter(self._tokens)

        def close(self):  # pragma: no cover - trivial
            self.closed = True

    dummy = DummyTokenizer([str(i) for i in range(TOTAL_TOKENS)])

    def fake_tokenizer(text: str, max_tokens: int = MAX_TOKENS) -> DummyTokenizer:
        del text, max_tokens
        return dummy

    monkeypatch.setattr(routers, "tokenize_preview", fake_tokenizer)

    async def run() -> None:
        initial = current_sse_tokens()
        resp = await routers.stream(ScoreReq(text="whatever"), DummyRequest())
        agen = resp.body_iterator
        await agen.__anext__()
        await agen.aclose()
        assert dummy.closed
        diff = current_sse_tokens() - initial
        assert diff < TOTAL_TOKENS

    asyncio.run(run())


def test_stream_sse_request_disconnect(monkeypatch) -> None:
    class DummyRequest:
        def __init__(self) -> None:
            self.calls = 0

        async def is_disconnected(self) -> bool:
            self.calls += 1
            return self.calls > 1

    class DummyTokenizer:
        def __init__(self, tokens: list[str]):
            self._tokens = tokens
            self.closed = False

        def __iter__(self):
            return iter(self._tokens)

        def close(self):  # pragma: no cover - trivial
            self.closed = True

    dummy = DummyTokenizer([str(i) for i in range(TOTAL_TOKENS)])

    def fake_tokenizer(text: str, max_tokens: int = MAX_TOKENS) -> DummyTokenizer:
        del text, max_tokens
        return dummy

    monkeypatch.setattr(routers, "tokenize_preview", fake_tokenizer)

    async def run() -> None:
        initial = current_sse_tokens()
        resp = await routers.stream(ScoreReq(text="whatever"), DummyRequest())
        agen = resp.body_iterator
        await agen.__anext__()  # start
        chunk = await agen.__anext__()  # first token
        assert "token" in chunk
        chunk = await agen.__anext__()  # should be end due to disconnect
        assert "end" in chunk
        with pytest.raises(StopAsyncIteration):
            await agen.__anext__()
        assert dummy.closed
        diff = current_sse_tokens() - initial
        assert diff == 1

    asyncio.run(run())
