import pytest
from fastapi.testclient import TestClient as SyncClient

from factsynth_ultimate.app import app


@pytest.mark.smoke
def test_ws_stream_basic():
    sc = SyncClient(app)
    with sc.websocket_connect("/ws/stream", headers={"x-api-key": "change-me"}) as ws:
        ws.send_text("ping")
        msg = ws.receive_text()
        assert isinstance(msg, str) and len(msg) > 0
