import time

import pytest
from fastapi.testclient import TestClient as SyncClient

from factsynth_ultimate.api import routers
from factsynth_ultimate.app import app

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


@pytest.mark.smoke
def test_ws_stream_basic():
    sc = SyncClient(app)
    with sc.websocket_connect("/ws/stream", headers={"x-api-key": "change-me"}) as ws:
        ws.send_text("ping")
        msg = ws.receive_text()
        assert isinstance(msg, str) and len(msg) > 0


def test_ws_stream_disconnect_closes_resources(monkeypatch):
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

    def fake_tokenize_preview(text: str, max_tokens: int = 128) -> DummyTokens:
        del text, max_tokens
        return DummyTokens()

    monkeypatch.setattr(routers, "tokenize_preview", fake_tokenize_preview)

    sc = SyncClient(app)
    with sc.websocket_connect("/ws/stream", headers={"x-api-key": "change-me"}) as ws:
        ws.send_text("ping")
        time.sleep(0.01)
        msg = ws.receive_json()
        assert msg == {"t": "a"}
        ws.close()

    assert retr.closed
