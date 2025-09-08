from __future__ import annotations
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from ..i18n import choose_language, translate

class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int = 2_000_000):
        super().__init__(app)
        self.max_bytes = max_bytes
    async def dispatch(self, request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > self.max_bytes:
            lang = choose_language(request)
            title = translate(lang, "payload_too_large")
            return JSONResponse(
                {"type": "about:blank", "title": title, "status": 413},
                status_code=413,
                media_type="application/problem+json",
            )
        return await call_next(request)
