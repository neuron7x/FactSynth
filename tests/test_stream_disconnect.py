import asyncio

from fastapi.testclient import TestClient

from factsynth_ultimate.api import routers
from factsynth_ultimate.app import create_app
from factsynth_ultimate.core.metrics import SSE_TOKENS
from factsynth_ultimate.schemas.requests import ScoreReq

TOTAL_TOKENS = 1000


def test_stream_sse_client_disconnect() -> None:
    text = " ".join(str(i) for i in range(TOTAL_TOKENS))
    total_tokens = TOTAL_TOKENS
    initial = SSE_TOKENS._value.get()
    with TestClient(create_app()) as client, client.stream(
        "POST",
        "/v1/stream",
        headers={"x-api-key": "change-me"},
        json={"text": text},
    ):
        # Do not consume the stream to simulate client disconnect.
        pass
    diff = SSE_TOKENS._value.get() - initial
    assert diff < total_tokens


def test_stream_sse_client_cancel(monkeypatch) -> None:
    class DummyTokenizer:
        def __init__(self, tokens: list[str]):
            self._tokens = tokens
            self.closed = False

        def __iter__(self):
            return iter(self._tokens)

        def close(self):  # pragma: no cover - trivial
            self.closed = True

    dummy = DummyTokenizer([str(i) for i in range(TOTAL_TOKENS)])

    def fake_tokenizer(text: str, max_tokens: int = 256) -> DummyTokenizer:
        del text, max_tokens
        return dummy

    monkeypatch.setattr(routers, "tokenize_preview", fake_tokenizer)

    async def run() -> None:
        total_tokens = TOTAL_TOKENS
        initial = SSE_TOKENS._value.get()
        resp = await routers.stream(ScoreReq(text="whatever"))
        agen = resp.body_iterator
        await agen.__anext__()
        await agen.aclose()
        assert dummy.closed
        diff = SSE_TOKENS._value.get() - initial
        assert diff < total_tokens

    asyncio.run(run())
