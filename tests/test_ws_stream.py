from fastapi.testclient import TestClient
from factsynth_ultimate.app import app

def test_ws_stream_smoke():
    c = TestClient(app)
    with c.websocket_connect("/ws/stream", headers={"x-api-key":"change-me"}) as ws:
        ws.send_text("hello world")
        msg = ws.receive_json()
        assert "t" in msg or "end" in msg
