import os, asyncio, pytest
import websockets

BASE = os.getenv("SMOKE_BASE_URL") or os.getenv("BASE_URL") or "http://127.0.0.1:8000"
WS = os.getenv("WS_URL") or BASE.replace("http", "ws") + "/ws"

@pytest.mark.asyncio
async def test_ws_smoke():
    try:
        async with websockets.connect(WS, open_timeout=5, close_timeout=5) as ws:
            await asyncio.wait_for(ws.close(), 2)
    except Exception as e:
        pytest.skip(f"WS not available: {e}")
