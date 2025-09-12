from __future__ import annotations

from contextlib import suppress

from fastapi import Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..i18n import choose_language, translate
from .metrics import REQUESTS


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(  # noqa: PLR0913
        self,
        app: ASGIApp,
        *,
        redis: Redis,
        per_key: int = 120,
        per_ip: int = 120,
        per_org: int = 120,
        key_header: str = "x-api-key",
        org_header: str = "x-organization",
        window: int = 60,
    ) -> None:
        super().__init__(app)
        self.redis = redis
        self.per_key = per_key
        self.per_ip = per_ip
        self.per_org = per_org
        self.key_header = key_header
        self.org_header = org_header
        self.window = window

    def _identifiers(self, request: Request) -> tuple[str, str, str]:
        api_key = request.headers.get(self.key_header) or "anon"
        ip = request.client.host if request.client else "anon"
        org = request.headers.get(self.org_header) or "anon"
        return api_key, ip, org

    async def _check(self, redis_key: str, limit: int) -> tuple[bool, int]:
        count = await self.redis.incr(redis_key)
        if count == 1:
            await self.redis.expire(redis_key, self.window)
        return count <= limit, count

    def _set_headers(self, response, limit: int, used: int) -> None:
        response.headers.setdefault("X-RateLimit-Limit", str(limit))
        response.headers.setdefault("X-RateLimit-Remaining", str(max(0, limit - used)))

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith(("/v1/healthz", "/metrics")):
            return await call_next(request)
        api_key, ip, org = self._identifiers(request)
        checks: dict[str, tuple[str, int]] = {
            "key": (f"rl:key:{api_key}", self.per_key),
            "ip": (f"rl:ip:{ip}", self.per_ip),
            "org": (f"rl:org:{org}", self.per_org),
        }
        counts: dict[str, int] = {}
        for name, (redis_key, limit) in checks.items():
            if limit <= 0:
                continue
            ok, count = await self._check(redis_key, limit)
            counts[name] = count
            if not ok:
                with suppress(Exception):
                    REQUESTS.labels(request.method, path, "429").inc()
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
                resp.headers["Retry-After"] = str(self.window)
                self._set_headers(resp, limit, count)
                return resp
        response = await call_next(request)
        if self.per_key > 0 and "key" in counts:
            self._set_headers(response, self.per_key, counts.get("key", 0))
        return response
