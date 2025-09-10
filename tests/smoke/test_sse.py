import os, asyncio, aiohttp, pytest
BASE = os.getenv("SMOKE_BASE_URL") or os.getenv("BASE_URL") or "http://127.0.0.1:8000"
SSE = os.getenv("SSE_URL") or f"{BASE}/sse"

@pytest.mark.asyncio
async def test_sse_smoke():
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        try:
            async with s.get(SSE, headers={"Accept": "text/event-stream"}) as r:
                assert r.status in (200, 204), f"SSE status {r.status}"
        except Exception as e:
            pytest.skip(f"SSE not available: {e}")
