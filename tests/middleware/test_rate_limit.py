from __future__ import annotations

import pytest
from fastapi import Request, Response

from factsynth_ultimate.core import rate_limit
from factsynth_ultimate.core.metrics import RATE_LIMIT_BLOCKS
from factsynth_ultimate.core.rate_limit import RateLimitMiddleware, RateQuota

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


class Clock:
    def __init__(self) -> None:
        self._value = 0.0

    def time(self) -> float:
        return self._value

    def advance(self, delta: float) -> None:
        self._value += delta


class FakeRedis:
    def __init__(self, now) -> None:
        self._now = now
        self._data: dict[str, dict[str, str]] = {}
        self._expiry: dict[str, float] = {}

    def _maybe_expire(self, key: str) -> None:
        deadline = self._expiry.get(key)
        if deadline is not None and self._now() >= deadline:
            self._data.pop(key, None)
            self._expiry.pop(key, None)

    async def hgetall(self, key: str) -> dict[str, str]:
        self._maybe_expire(key)
        return self._data.get(key, {}).copy()

    async def hset(self, key: str, mapping) -> None:  # noqa: ANN001
        self._maybe_expire(key)
        encoded = {k: str(v) for k, v in mapping.items()}
        self._data.setdefault(key, {}).update(encoded)

    async def expire(self, key: str, ttl: int) -> None:
        self._expiry[key] = self._now() + ttl

    async def ping(self) -> bool:  # pragma: no cover - trivial behaviour
        return True

    def keys(self) -> set[str]:
        for key in list(self._data):
            self._maybe_expire(key)
        return set(self._data.keys())


async def _empty_receive():  # pragma: no cover - ASGI plumbing
    return {"type": "http.request", "body": b"", "more_body": False}


def make_request(headers: dict[str, str], client_ip: str = "1.2.3.4", path: str = "/v1/test") -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "root_path": "",
        "scheme": "http",
        "query_string": b"",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": (client_ip, 1234),
        "server": ("testserver", 80),
    }
    return Request(scope, _empty_receive)


@pytest.fixture(autouse=True)
def _reset_metrics():
    RATE_LIMIT_BLOCKS._metrics.clear()  # type: ignore[attr-defined]
    yield
    RATE_LIMIT_BLOCKS._metrics.clear()  # type: ignore[attr-defined]


@pytest.fixture
def clock(monkeypatch) -> Clock:
    clk = Clock()
    monkeypatch.setattr(rate_limit.time, "time", clk.time)
    return clk


def _middleware(redis: FakeRedis, **kwargs) -> RateLimitMiddleware:
    return RateLimitMiddleware(  # type: ignore[arg-type]
        lambda scope, receive, send: None,
        redis=redis,
        **kwargs,
        health_check_interval=0.0,
    )


@pytest.mark.anyio
async def test_all_limits_allow(clock: Clock) -> None:
    redis = FakeRedis(clock.time)
    middleware = _middleware(
        redis,
        api=RateQuota(2, 1.0),
        ip=RateQuota(2, 1.0),
        org=RateQuota(2, 1.0),
    )
    request = make_request({"x-api-key": "key", "x-organization": "org"})

    async def call_next(_: Request) -> Response:
        return Response(status_code=200)

    response = await middleware.dispatch(request, call_next)
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "6"
    assert response.headers["X-RateLimit-Remaining"] == "3"
    assert redis.keys() == {"api:key", "ip:1.2.3.4", "org:org"}


@pytest.mark.anyio
async def test_block_when_api_exhausted(clock: Clock) -> None:
    redis = FakeRedis(clock.time)
    middleware = _middleware(
        redis,
        api=RateQuota(1, 1.0),
        ip=RateQuota(2, 1.0),
        org=RateQuota(2, 1.0),
    )
    request = make_request({"x-api-key": "alpha", "x-organization": "team"})

    async def call_next(_: Request) -> Response:
        return Response(status_code=200)

    await middleware.dispatch(request, call_next)
    response = await middleware.dispatch(request, call_next)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "1"
    assert response.headers["X-RateLimit-Limit"] == "5"
    assert response.headers["X-RateLimit-Remaining"] == "2"
    assert RATE_LIMIT_BLOCKS.labels("api")._value.get() == 1  # type: ignore[attr-defined]


@pytest.mark.anyio
async def test_block_when_ip_exhausted(clock: Clock) -> None:
    redis = FakeRedis(clock.time)
    middleware = _middleware(
        redis,
        api=RateQuota(3, 1.0),
        ip=RateQuota(1, 1.0),
        org=RateQuota(3, 1.0),
    )
    request = make_request({"x-api-key": "beta", "x-organization": "team"}, client_ip="10.0.0.1")

    async def call_next(_: Request) -> Response:
        return Response(status_code=200)

    await middleware.dispatch(request, call_next)
    response = await middleware.dispatch(request, call_next)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "1"
    assert response.headers["X-RateLimit-Limit"] == "7"
    assert response.headers["X-RateLimit-Remaining"] == "4"
    assert RATE_LIMIT_BLOCKS.labels("ip")._value.get() == 1  # type: ignore[attr-defined]


@pytest.mark.anyio
async def test_block_when_org_exhausted(clock: Clock) -> None:
    redis = FakeRedis(clock.time)
    middleware = _middleware(
        redis,
        api=RateQuota(3, 1.0),
        ip=RateQuota(3, 1.0),
        org=RateQuota(1, 1.0),
    )
    request = make_request({"x-api-key": "gamma", "x-organization": "org"})

    async def call_next(_: Request) -> Response:
        return Response(status_code=200)

    await middleware.dispatch(request, call_next)
    response = await middleware.dispatch(request, call_next)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "1"
    assert response.headers["X-RateLimit-Limit"] == "7"
    assert response.headers["X-RateLimit-Remaining"] == "4"
    assert RATE_LIMIT_BLOCKS.labels("org")._value.get() == 1  # type: ignore[attr-defined]


@pytest.mark.anyio
async def test_retry_after_uses_longest_wait(clock: Clock) -> None:
    redis = FakeRedis(clock.time)
    middleware = _middleware(
        redis,
        api=RateQuota(1, 0.25),
        ip=RateQuota(1, 1.0),
        org=RateQuota(1, 0.5),
    )
    request = make_request({"x-api-key": "delta", "x-organization": "dept"})

    async def call_next(_: Request) -> Response:
        return Response(status_code=200)

    await middleware.dispatch(request, call_next)
    response = await middleware.dispatch(request, call_next)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "4"
    assert RATE_LIMIT_BLOCKS.labels("api")._value.get() == 1  # type: ignore[attr-defined]
    assert RATE_LIMIT_BLOCKS.labels("ip")._value.get() == 1  # type: ignore[attr-defined]
    assert RATE_LIMIT_BLOCKS.labels("org")._value.get() == 1  # type: ignore[attr-defined]


@pytest.mark.anyio
async def test_block_when_all_limits_exhausted(clock: Clock) -> None:
    redis = FakeRedis(clock.time)
    middleware = _middleware(
        redis,
        api=RateQuota(1, 1.0),
        ip=RateQuota(1, 1.0),
        org=RateQuota(1, 1.0),
    )
    request = make_request({"x-api-key": "theta", "x-organization": "squad"})

    async def call_next(_: Request) -> Response:
        return Response(status_code=200)

    await middleware.dispatch(request, call_next)
    response = await middleware.dispatch(request, call_next)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "1"
    assert response.headers["X-RateLimit-Limit"] == "3"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert RATE_LIMIT_BLOCKS.labels("api")._value.get() == 1  # type: ignore[attr-defined]
    assert RATE_LIMIT_BLOCKS.labels("ip")._value.get() == 1  # type: ignore[attr-defined]
    assert RATE_LIMIT_BLOCKS.labels("org")._value.get() == 1  # type: ignore[attr-defined]
