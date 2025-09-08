from __future__ import annotations
from time import monotonic
from collections import defaultdict, deque
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .metrics import REQUESTS

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, per_minute: int = 120, key_header: str = "x-api-key"):
        super().__init__(app)
        self.per_minute = per_minute
        self.key_header = key_header
        self.buckets = defaultdict(deque)

    def _key(self, request: Request) -> str:
        return request.headers.get(self.key_header) or (request.client.host if request.client else "anon")

    def _set_headers(self, response, used: int) -> None:
        limit = self.per_minute
        response.headers.setdefault("X-RateLimit-Limit", str(limit))
        response.headers.setdefault("X-RateLimit-Remaining", str(max(0, limit - used)))

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith(("/v1/healthz","/metrics")):
            return await call_next(request)
        key = self._key(request)
        now = monotonic()
        window_start = now - 60.0
        q = self.buckets[key]
        while q and q[0] < window_start:
            q.popleft()
        if len(q) >= self.per_minute:
            try: REQUESTS.labels(request.method, path, "429").inc()
            except Exception: pass
            resp = JSONResponse({"type":"about:blank","title":"Too Many Requests","status":429}, status_code=429, media_type="application/problem+json")
            resp.headers["Retry-After"] = "60"
            self._set_headers(resp, used=len(q))
            return resp
        q.append(now)
        response = await call_next(request)
        self._set_headers(response, used=len(q))
        # періодичне прибирання старих ключів
        if len(self.buckets) > 10000 and not q:  # грубе обмеження
            self.buckets.pop(key, None)
        return response
