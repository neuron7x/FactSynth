"""Token bucket rate limiting middleware."""

from __future__ import annotations

import logging
import math
import time
from collections.abc import Awaitable, Callable, Iterable, Mapping
from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar, cast

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..i18n import choose_language, translate
from ..store.memory import MemoryStore
from .metrics import RATE_LIMIT_BLOCKS, REQUESTS

if TYPE_CHECKING:
    from .settings import Settings

T = TypeVar("T")


def _load_rate_settings() -> Settings:
    """Load application settings lazily to avoid circular imports."""

    from .settings import load_settings  # Imported here to avoid cycles.

    return load_settings()


@dataclass(frozen=True)
class RateQuota:
    """Configuration for a token bucket rate limit."""

    burst: int
    sustain: float

    def __post_init__(self) -> None:
        if self.burst < 0:
            msg = "burst must be non-negative"
            raise ValueError(msg)
        if self.sustain <= 0:
            msg = "sustain must be positive"
            raise ValueError(msg)

    @property
    def enabled(self) -> bool:
        """Return ``True`` if this quota should be enforced."""

        return self.burst > 0


@dataclass
class _RateCheck:
    """State for a single rate limit evaluation."""

    name: str
    redis_key: str
    quota: RateQuota
    allowed: bool
    tokens: float


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token buckets in Redis."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        redis: Redis[Any],
        api: RateQuota | None = None,
        ip: RateQuota | None = None,
        org: RateQuota | None = None,
        burst: int | None = None,
        sustain: float | None = None,
        key_header: str = "x-api-key",
        org_header: str = "x-organization",
        ttl: int = 300,
        memory_store: MemoryStore | None = None,
        fallback_timeout: float = 30.0,
    ) -> None:
        """Configure middleware with independent quotas for API/IP/org."""

        super().__init__(app)
        default_burst = burst if burst is not None else 60
        default_sustain = sustain if sustain is not None else 1.0

        def _default_quota() -> RateQuota:
            return RateQuota(int(default_burst), float(default_sustain))

        settings_obj = None

        def _settings_quota(attr: str) -> RateQuota:
            nonlocal settings_obj
            if settings_obj is None:
                settings_obj = _load_rate_settings()
            quota_obj = getattr(settings_obj, attr)
            return RateQuota(int(quota_obj.burst), float(quota_obj.sustain))

        use_settings_defaults = burst is None and sustain is None

        self.redis = redis
        self.ttl = ttl
        self.key_header = key_header
        self.org_header = org_header
        self.api_quota = api or (
            _settings_quota("rates_api") if use_settings_defaults else _default_quota()
        )
        self.ip_quota = ip or (
            _settings_quota("rates_ip") if use_settings_defaults else _default_quota()
        )
        self.org_quota = org or (
            _settings_quota("rates_org") if use_settings_defaults else _default_quota()
        )
        self._memory_store = memory_store or MemoryStore()
        self._fallback_timeout = max(0.0, float(fallback_timeout))
        self._fallback_until = 0.0
        self._using_memory = False
        self._logger = logging.getLogger(__name__)

    def _should_use_redis(self) -> bool:
        if self._fallback_timeout <= 0:
            return True
        if not self._using_memory:
            return True
        return time.monotonic() >= self._fallback_until

    def _activate_fallback(self, exc: Exception) -> None:
        if self._fallback_timeout <= 0:
            raise exc
        now = time.monotonic()
        self._fallback_until = now + self._fallback_timeout
        if not self._using_memory:
            self._logger.warning(
                "Redis backend unavailable, using in-memory fallback for %.1fs: %s",
                self._fallback_timeout,
                exc,
            )
        self._using_memory = True

    def _on_redis_success(self) -> None:
        if self._using_memory:
            self._using_memory = False
            self._fallback_until = 0.0
            self._logger.info("Redis backend recovered; resuming primary store")

    async def _call_store(self, method: str, *args: Any, **kwargs: Any) -> T:
        use_redis = self._should_use_redis()
        store = self.redis if use_redis else self._memory_store
        try:
            func = cast(Callable[..., Awaitable[T]], getattr(store, method))
            result = await func(*args, **kwargs)
        except (TimeoutError, RedisError, OSError) as exc:
            if use_redis and self._fallback_timeout > 0:
                self._activate_fallback(exc)
                fallback_func = cast(
                    Callable[..., Awaitable[T]], getattr(self._memory_store, method)
                )
                return await fallback_func(*args, **kwargs)
            raise
        else:
            if use_redis:
                self._on_redis_success()
            return result

    async def _take(
        self,
        redis_key: str,
        quota: RateQuota,
        *,
        consume: bool = True,
    ) -> tuple[bool, float]:
        """Attempt to take a token from the bucket identified by ``redis_key``."""

        now = time.time()
        data: Mapping[str | bytes, str | bytes] = await self._call_store(
            "hgetall", redis_key
        )
        raw_tokens = data.get("tokens") or data.get(b"tokens")
        raw_ts = data.get("ts") or data.get(b"ts")
        tokens = float(raw_tokens) if raw_tokens is not None else float(quota.burst)
        ts = float(raw_ts) if raw_ts is not None else now
        delta = max(0.0, now - ts)
        tokens = min(float(quota.burst), tokens + delta * quota.sustain)
        allowed = tokens >= 1.0
        new_tokens = tokens - 1.0 if allowed and consume else tokens
        await self._call_store(
            "hset",
            redis_key,
            mapping={"tokens": new_tokens if consume and allowed else tokens, "ts": now},
        )
        await self._call_store("expire", redis_key, self.ttl)
        return allowed, new_tokens if consume and allowed else tokens

    @staticmethod
    def _set_headers(response: Response, limit: int, remaining: float) -> None:
        """Populate standard rate limit headers on ``response``."""

        response.headers.setdefault("X-RateLimit-Limit", str(limit))
        response.headers.setdefault("X-RateLimit-Remaining", str(max(0, int(remaining))))

    @staticmethod
    def _redis_key(prefix: str, identifier: str) -> str:
        """Return a normalized Redis key for a specific identifier."""

        ident = str(identifier).strip()
        if not ident:
            ident = "anon"
        return f"{prefix}:{ident}"

    def _limits(self, api_key: str, ip: str, org: str) -> list[tuple[str, str, RateQuota]]:
        """Return Redis key and quota triples for the request."""

        triples: list[tuple[str, str, RateQuota]] = []
        for name, ident, quota in (
            ("api", api_key, self.api_quota),
            ("ip", ip, self.ip_quota),
            ("org", org, self.org_quota),
        ):
            if quota.enabled:
                triples.append((name, self._redis_key(name, ident), quota))
        return triples

    @staticmethod
    def _retry_after(checks: Iterable[_RateCheck]) -> int:
        """Return the number of seconds a client should wait before retrying."""

        delays: list[float] = []
        for check in checks:
            if check.allowed:
                continue
            deficit = max(0.0, 1.0 - check.tokens)
            delay = deficit / check.quota.sustain if check.quota.sustain else 0.0
            if delay > 0:
                delays.append(delay)
        if not delays:
            return 1
        return max(1, math.ceil(max(delays)))

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Apply rate limits before delegating to the next middleware."""

        api_key = request.headers.get(self.key_header)
        if not api_key:
            return await call_next(request)

        client = request.client
        ip = client.host if client else "anon"
        org = request.headers.get(self.org_header) or "anon"
        route = request.url.path

        limits = self._limits(api_key, ip, org)
        if not limits:
            return await call_next(request)

        checks: list[_RateCheck] = []
        for name, redis_key, quota in limits:
            allowed, tokens = await self._take(redis_key, quota, consume=False)
            checks.append(_RateCheck(name, redis_key, quota, allowed, tokens))

        limit_total = sum(check.quota.burst for check in checks)

        if all(check.allowed for check in checks):
            remaining_total = 0.0
            for idx, check in enumerate(checks):
                _, remaining = await self._take(check.redis_key, check.quota, consume=True)
                remaining = max(0.0, remaining)
                remaining_total += remaining
                checks[idx] = _RateCheck(check.name, check.redis_key, check.quota, True, remaining)
            response = await call_next(request)
            self._set_headers(response, limit_total, remaining_total)
            return response

        for check in checks:
            if not check.allowed:
                with suppress(Exception):
                    RATE_LIMIT_BLOCKS.labels(check.name).inc()
        retry_after = self._retry_after(checks)
        remaining_total = sum(max(0.0, check.tokens) for check in checks)
        with suppress(Exception):
            REQUESTS.labels(request.method, route, "429").inc()
        lang = choose_language(request)
        title = translate(lang, "too_many_requests")
        detail = "Request rate limit exceeded"
        problem = {
            "type": "about:blank",
            "title": title,
            "status": 429,
            "detail": detail,
            "trace_id": getattr(request.state, "request_id", ""),
        }
        resp = JSONResponse(
            problem,
            status_code=429,
            media_type="application/problem+json",
        )
        resp.headers["Retry-After"] = str(retry_after)
        self._set_headers(resp, limit_total, remaining_total)
        return resp
