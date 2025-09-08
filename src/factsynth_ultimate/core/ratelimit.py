from __future__ import annotations

from collections import defaultdict, deque
from contextlib import suppress
from time import monotonic
from typing import DefaultDict, Deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .i18n import translate
from .metrics import REQUESTS


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        per_minute: int = 120,
        key_header: str = "x-api-key",
        bucket_ttl: float = 300.0,
        cleanup_interval: float = 60.0,
    ):
        super().__init__(app)
        if per_minute <= 0:
            raise ValueError("per_minute must be positive")
        if bucket_ttl <= 0:
            raise ValueError("bucket_ttl must be positive")
        if cleanup_interval <= 0:
            raise ValueError("cleanup_interval must be positive")
        self.per_minute = per_minute
        self.key_header = key_header
        self.bucket_ttl = bucket_ttl
        self.cleanup_interval = cleanup_interval
        self.buckets: DefaultDict[str, Deque[float]] = defaultdict(deque)
        self._next_cleanup = monotonic() + cleanup_interval

    def _key(self, request: Request) -> str:
        return request.headers.get(self.key_header) or (request.client.host if request.client else "anon")

    def _set_headers(self, response, used: int) -> None:
        limit = self.per_minute
        response.headers.setdefault("X-RateLimit-Limit", str(limit))
        response.headers.setdefault("X-RateLimit-Remaining", str(max(0, limit - used)))

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith(("/v1/healthz", "/metrics")):
            return await call_next(request)
        key = self._key(request)
        now = monotonic()
        if now >= self._next_cleanup:
            cutoff = now - self.bucket_ttl
            for k, dq in list(self.buckets.items()):
                if dq and dq[-1] < cutoff:
                    del self.buckets[k]
            self._next_cleanup = now + self.cleanup_interval
        window_start = now - 60.0
        q = self.buckets[key]
        while q and q[0] < window_start:
            q.popleft()
        if len(q) >= self.per_minute:
            title = translate("Too Many Requests", request.headers.get("accept-language"))
            resp = JSONResponse(
                {"type": "about:blank", "title": title, "status": 429},
                status_code=429,
                media_type="application/problem+json",
            )
            resp.headers["Retry-After"] = "60"
            self._set_headers(resp, used=len(q))
            with suppress(Exception):
                REQUESTS.labels(request.method, path, "429").inc()
            return resp
        q.append(now)
        response = await call_next(request)
        self._set_headers(response, used=len(q))
        with suppress(Exception):
            REQUESTS.labels(request.method, path, str(response.status_code)).inc()
        return response
