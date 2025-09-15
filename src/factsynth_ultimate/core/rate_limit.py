"""Token bucket rate limiting middleware."""

from __future__ import annotations

import math
import time
from contextlib import suppress
from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..i18n import choose_language, translate
from .metrics import RATE_LIMIT_BLOCKS, REQUESTS


@dataclass(frozen=True)
class RateQuota:
    """Configuration for a token bucket rate limit."""

    burst: int
    sustain: float

    def __post_init__(self) -> None:  # noqa: D401
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
        redis: Redis,
        api: RateQuota | None = None,
        ip: RateQuota | None = None,
        org: RateQuota | None = None,
        burst: int | None = None,
        sustain: float | None = None,
        key_header: str = "x-api-key",
        org_header: str = "x-organization",
        ttl: int = 300,
    ) -> None:
        """Configure middleware with independent quotas for API/IP/org."""

        super().__init__(app)
        default_burst = burst if burst is not None else 60
        default_sustain = sustain if sustain is not None else 1.0
        default_quota = api or RateQuota(default_burst, float(default_sustain))
        self.redis = redis
        self.ttl = ttl
        self.key_header = key_header
        self.org_header = org_header
        self.api_quota = default_quota
        self.ip_quota = ip or default_quota
        self.org_quota = org or default_quota

    async def _take(
        self,
        redis_key: str,
        quota: RateQuota,
        *,
        consume: bool = True,
    ) -> tuple[bool, float]:
        """Attempt to take a token from the bucket identified by ``redis_key``."""

        now = time.time()
        data = await self.redis.hgetall(redis_key)
        raw_tokens = data.get("tokens") or data.get(b"tokens")
        raw_ts = data.get("ts") or data.get(b"ts")
        tokens = float(raw_tokens) if raw_tokens is not None else float(quota.burst)
        ts = float(raw_ts) if raw_ts is not None else now
        delta = max(0.0, now - ts)
        tokens = min(float(quota.burst), tokens + delta * quota.sustain)
        allowed = tokens >= 1.0
        new_tokens = tokens - 1.0 if allowed and consume else tokens
        await self.redis.hset(
            redis_key,
            mapping={"tokens": new_tokens if consume and allowed else tokens, "ts": now},
        )
        await self.redis.expire(redis_key, self.ttl)
        return allowed, new_tokens if consume and allowed else tokens

    @staticmethod
    def _set_headers(response: Response, limit: int, remaining: float) -> None:
        """Populate standard rate limit headers on ``response``."""

        response.headers.setdefault("X-RateLimit-Limit", str(limit))
        response.headers.setdefault("X-RateLimit-Remaining", str(max(0, int(remaining))))

    def _limits(self, api_key: str, ip: str, org: str) -> list[tuple[str, str, RateQuota]]:
        """Return Redis key and quota triples for the request."""

        triples: list[tuple[str, str, RateQuota]] = []
        for name, ident, quota in (
            ("api", api_key, self.api_quota),
            ("ip", ip, self.ip_quota),
            ("org", org, self.org_quota),
        ):
            if quota.enabled:
                triples.append((name, f"{name}:{ident}", quota))
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
