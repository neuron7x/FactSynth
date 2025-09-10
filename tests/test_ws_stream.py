import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from factsynth_ultimate.app import app

UNAUTHORIZED = 4401


def test_ws_stream_smoke():
    c = TestClient(app)
    with c.websocket_connect("/ws/stream", headers={"x-api-key":"change-me"}) as ws:
        ws.send_text("hello world")
        msg = ws.receive_json()
        assert "t" in msg or "end" in msg


def test_ws_stream_bad_key():
    c = TestClient(app)
    with (
        c.websocket_connect("/ws/stream", headers={"x-api-key": "bad"}) as ws,
        pytest.raises(WebSocketDisconnect) as exc_info,
    ):
        ws.receive_json()
    assert exc_info.value.code == UNAUTHORIZED


def test_ws_stream_bad_key_on_send():
    c = TestClient(app)
    with (
        c.websocket_connect("/ws/stream", headers={"x-api-key": "wrong"}) as ws,
        pytest.raises(WebSocketDisconnect) as exc_info,
    ):
        ws.send_text("ignored")
        ws.receive_json()
    assert exc_info.value.code == UNAUTHORIZED
