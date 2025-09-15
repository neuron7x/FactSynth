import asyncio

import pytest
from fastapi.testclient import TestClient as SyncClient

from factsynth_ultimate.api import routers
from factsynth_ultimate.app import app
from factsynth_ultimate.core.metrics import current_sse_tokens

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


@pytest.mark.smoke
def test_ws_stream_basic():
    sc = SyncClient(app)
    with sc.websocket_connect("/ws/stream", headers={"x-api-key": "change-me"}) as ws:
        ws.send_text("ping")
        msg = ws.receive_text()
        assert isinstance(msg, str) and len(msg) > 0


def test_ws_stream_slow_reader():
    sc = SyncClient(app)
    with sc.websocket_connect("/ws/stream", headers={"x-api-key": "change-me"}) as ws:
        ws.send_text("alpha beta gamma")
        for tok in ("alpha", "beta", "gamma"):
            assert ws.receive_json() == {"t": tok}
        assert ws.receive_json() == {"end": True}


def test_ws_stream_disconnect_closes_resources(monkeypatch):
    done = asyncio.Event()

    class DummyRetriever:
        def __init__(self) -> None:
            self.closed = False

        async def aclose(self) -> None:
            self.closed = True
            done.set()

    retr = DummyRetriever()

    class DummyTokens(list):
        def __init__(self) -> None:
            super().__init__(["a", "b", "c"])
            self.retriever = retr

    def fake_tokenize_preview(text: str, max_tokens: int = 128) -> DummyTokens:
        del text, max_tokens
        return DummyTokens()

    monkeypatch.setattr(routers, "tokenize_preview", fake_tokenize_preview)

    calls = 0

    def fake_is_client_connected(_ws):
        nonlocal calls
        calls += 1
        return False

    monkeypatch.setattr(routers, "is_client_connected", fake_is_client_connected)

    sc = SyncClient(app)
    initial = current_sse_tokens()
    with sc.websocket_connect("/ws/stream", headers={"x-api-key": "change-me"}) as ws:
        ws.send_text("ping")
        ws.close()
    asyncio.get_event_loop().run_until_complete(asyncio.wait_for(done.wait(), timeout=1))

    diff = current_sse_tokens() - initial
    assert retr.closed
    assert diff == 0
    assert calls >= 1
