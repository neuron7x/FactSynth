from fastapi.testclient import TestClient
import pytest

from factsynth_ultimate.app import create_app
from factsynth_ultimate.core.metrics import SSE_TOKENS
from factsynth_ultimate.schemas.requests import ScoreReq
from factsynth_ultimate.api import routers


def test_stream_sse_client_disconnect() -> None:
    text = " ".join(str(i) for i in range(1000))
    total_tokens = 1000
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


@pytest.mark.asyncio
async def test_stream_sse_client_cancel(monkeypatch) -> None:
    class DummyTokenizer:
        def __init__(self, tokens: list[str]):
            self._tokens = tokens
            self.closed = False

        def __iter__(self):
            return iter(self._tokens)

        def close(self):  # pragma: no cover - trivial
            self.closed = True

    dummy = DummyTokenizer([str(i) for i in range(1000)])

    monkeypatch.setattr(routers, "tokenize_preview", lambda text, max_tokens=256: dummy)

    total_tokens = 1000
    initial = SSE_TOKENS._value.get()
    resp = await routers.stream(ScoreReq(text="whatever"))
    agen = resp.body_iterator
    await agen.__anext__()
    await agen.aclose()
    assert dummy.closed
    diff = SSE_TOKENS._value.get() - initial
    assert diff < total_tokens
