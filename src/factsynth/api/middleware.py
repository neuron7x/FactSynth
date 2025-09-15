from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware

from factsynth.metrics.embodied import ReqTimer


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):  # type: ignore[override]
        with ReqTimer():
            response = await call_next(request)
        return response
