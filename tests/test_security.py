import asyncio
import pytest
from fastapi import HTTPException

from src.factsynth_ultimate import security


def test_rate_limiter_concurrent():
    async def run_test():
        security._BUCKET.clear()
        security._BUCKET_QUEUE.clear()
        security.S.RATE_MAX_REQ = 1
        security.S.RATE_WINDOW_SEC = 10
        key = "k"

        async def worker():
            try:
                await security.rate_limiter(x_api_key=key)
                return True
            except HTTPException:
                return False

        results = await asyncio.gather(*(worker() for _ in range(2)))
        assert results.count(True) == 1
        assert results.count(False) == 1

    asyncio.run(run_test())


def test_rate_limiter_key_expiry(monkeypatch):
    async def run_test():
        security._BUCKET.clear()
        security._BUCKET_QUEUE.clear()
        security.S.RATE_MAX_REQ = 1
        security.S.RATE_WINDOW_SEC = 10

        now = 1000
        monkeypatch.setattr(security, "time", lambda: now)
        await security.rate_limiter(x_api_key="k1")
        assert "k1" in security._BUCKET

        now += 11
        monkeypatch.setattr(security, "time", lambda: now)
        await security.rate_limiter(x_api_key="k2")
        assert "k1" not in security._BUCKET

    asyncio.run(run_test())
