"""Token bucket rate limiting middleware.

Counts requests per API key and route combination
with a TTL of 300 seconds and supports burst/sustain quotas.
"""

from __future__ import annotations

import math
import time
from contextlib import suppress
from typing import Awaitable, Callable, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..i18n import choose_language, translate
from .metrics import REQUESTS

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using a token bucket in Redis."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        redis: Redis,
        burst: int = 60,
        sustain: float = 1.0,
        key_header: str = "x-api-key",
        ttl: int = 300,
    ) -> None:
        """Configure middleware with burst and sustain quotas."""

        super().__init__(app)
        self.redis = redis
        self.burst = burst
        self.sustain = sustain
        self.key_header = key_header
        self.ttl = ttl

    async def _take(self, redis_key: str) -> Tuple[bool, float]:
        """Attempt to take a token from the bucket."""

        now = time.time()
        data = await self.redis.hgetall(redis_key)
        raw_tokens = data.get("tokens") or data.get(b"tokens")
        raw_ts = data.get("ts") or data.get(b"ts")
        tokens = float(raw_tokens) if raw_tokens is not None else float(self.burst)
        ts = float(raw_ts) if raw_ts is not None else now
        delta = max(0.0, now - ts)
        tokens = min(self.burst, tokens + delta * self.sustain)
        allowed = tokens >= 1.0
        if allowed:
            tokens -= 1.0
        await self.redis.hset(redis_key, mapping={"tokens": tokens, "ts": now})
        await self.redis.expire(redis_key, self.ttl)
        return allowed, tokens

    def _set_headers(self, response: Response, remaining: float) -> None:
        """Populate standard rate limit headers on ``response``."""

        response.headers.setdefault("X-RateLimit-Limit", str(self.burst))
        response.headers.setdefault("X-RateLimit-Remaining", str(max(0, int(remaining))))

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Apply rate limits before delegating to the next middleware."""

        api_key = request.headers.get(self.key_header)
        if not api_key:
            return await call_next(request)
        route = request.url.path
        redis_key = f"rl:{api_key}:{route}"
        allowed, tokens = await self._take(redis_key)
        if not allowed:
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
            retry_after = max(1, math.ceil((1 - tokens) / self.sustain))
            resp = JSONResponse(
                problem,
                status_code=429,
                media_type="application/problem+json",
            )
            resp.headers["Retry-After"] = str(retry_after)
            self._set_headers(resp, tokens)
            return resp
        response = await call_next(request)
        self._set_headers(response, tokens)
        return response
