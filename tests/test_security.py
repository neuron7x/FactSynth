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


def test_api_key_auth_audience_mismatch(monkeypatch):
    async def run_test():
        class DummyJWT:
            @staticmethod
            def decode(token, key, algorithms):
                return {"aud": ["other"]}

        monkeypatch.setattr(security, "jwt", DummyJWT)
        monkeypatch.setattr(security.S, "JWT_PUBLIC_KEY", "pub")
        monkeypatch.setattr(security.S, "JWT_REQUIRED_AUD", "expected")

        with pytest.raises(HTTPException) as exc:
            await security.api_key_auth(authorization="Bearer token")
        assert exc.value.status_code == 403
        assert exc.value.detail == "jwt_audience_mismatch"

    asyncio.run(run_test())


def test_rate_limiter_exhaustion(monkeypatch):
    async def run_test():
        security._BUCKET.clear()
        security._BUCKET_QUEUE.clear()
        security.S.RATE_MAX_REQ = 2
        security.S.RATE_WINDOW_SEC = 10

        now = 1000
        monkeypatch.setattr(security, "time", lambda: now)

        key = "k"
        await security.rate_limiter(x_api_key=key)
        await security.rate_limiter(x_api_key=key)
        with pytest.raises(HTTPException) as exc:
            await security.rate_limiter(x_api_key=key)
        assert exc.value.status_code == 429

    asyncio.run(run_test())
