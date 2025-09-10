import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from factsynth_ultimate.app import app

UNAUTHORIZED = 4401
TOKENS_COUNT = 3


def test_ws_stream_tokens_complete():
    c = TestClient(app)
    with c.websocket_connect("/ws/stream", headers={"x-api-key": "change-me"}) as ws:
        ws.send_text("one two")
        msgs = []
        while True:
            msg = ws.receive_json()
            msgs.append(msg)
            if msg.get("end"):
                break

    assert msgs[0]["t"] == "one"
    assert msgs[1]["t"] == "two"
    assert msgs[2] == {"end": True}
    assert len(msgs) == TOKENS_COUNT


def test_ws_stream_bad_key():
    c = TestClient(app)
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        c.websocket_connect("/ws/stream", headers={"x-api-key": "bad"}),
    ):
        pass
    assert exc_info.value.code == UNAUTHORIZED


def test_ws_stream_bad_key_on_send():
    c = TestClient(app)
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        c.websocket_connect("/ws/stream", headers={"x-api-key": "wrong"}),
    ):
        pass
    assert exc_info.value.code == UNAUTHORIZED
