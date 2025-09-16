from __future__ import annotations

import pytest
from redis.exceptions import RedisError

from factsynth_ultimate.core import rate_limit
from factsynth_ultimate.store.memory import MemoryStore
from factsynth_ultimate.store.redis import check_health


pytestmark = pytest.mark.anyio


class Clock:
    def __init__(self) -> None:
        self._value = 0.0

    def time(self) -> float:
        return self._value

    def monotonic(self) -> float:
        return self._value

    def advance(self, delta: float) -> None:
        self._value += delta


class FlakyRedis:
    """Redis stub that fails a fixed number of times before succeeding."""

    def __init__(self, failures: int, delegate: MemoryStore) -> None:
        self._failures = failures
        self._delegate = delegate

    def _maybe_fail(self) -> None:
        if self._failures > 0:
            self._failures -= 1
            raise RedisError("boom")

    async def hgetall(self, key: str):
        self._maybe_fail()
        return await self._delegate.hgetall(key)

    async def hset(self, key: str, mapping):  # noqa: ANN001
        self._maybe_fail()
        return await self._delegate.hset(key, mapping)

    async def expire(self, key: str, ttl: int):
        self._maybe_fail()
        return await self._delegate.expire(key, ttl)


class BrokenRedis:
    async def ping(self) -> None:  # pragma: no cover - simple stub
        raise RedisError("offline")


@pytest.fixture
def clock(monkeypatch):
    clk = Clock()
    monkeypatch.setattr(rate_limit.time, "time", clk.time)
    monkeypatch.setattr(rate_limit.time, "monotonic", clk.monotonic)
    return clk


def _middleware(redis, memory_store, fallback_timeout: float = 10.0):
    quota = rate_limit.RateQuota(5, 1.0)
    return rate_limit.RateLimitMiddleware(
        lambda scope, receive, send: None,
        redis=redis,
        api=quota,
        ip=quota,
        org=quota,
        ttl=60,
        memory_store=memory_store,
        fallback_timeout=fallback_timeout,
    )


@pytest.mark.anyio
async def test_switches_to_memory_on_failure(clock):
    memory_backend = MemoryStore(now=clock.monotonic)
    redis_backend = MemoryStore(now=clock.monotonic)
    redis = FlakyRedis(1, redis_backend)
    middleware = _middleware(redis, memory_backend)

    allowed, _ = await middleware._take("bucket", middleware.api_quota)
    assert allowed is True
    assert middleware._using_memory is True
    assert middleware._fallback_until > clock.monotonic()
    assert await memory_backend.hgetall("bucket")
    assert await redis_backend.hgetall("bucket") == {}

    # second call still uses the in-memory backend while fallback is active
    await middleware._take("bucket", middleware.api_quota)
    assert middleware._using_memory is True


@pytest.mark.anyio
async def test_recovers_after_timeout(clock):
    memory_backend = MemoryStore(now=clock.monotonic)
    redis_backend = MemoryStore(now=clock.monotonic)
    redis = FlakyRedis(1, redis_backend)
    middleware = _middleware(redis, memory_backend, fallback_timeout=5.0)

    await middleware._take("bucket", middleware.api_quota)
    assert middleware._using_memory is True

    clock.advance(10.0)
    allowed, _ = await middleware._take("bucket", middleware.api_quota)
    assert allowed is True
    assert middleware._using_memory is False
    redis_data = await redis_backend.hgetall("bucket")
    assert "tokens" in redis_data


@pytest.mark.anyio
async def test_check_health_reports_failure():
    client = BrokenRedis()
    assert await check_health(client) is False
