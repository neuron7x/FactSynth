from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..i18n import choose_language, translate


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int = 2_000_000):
        super().__init__(app)
        self.max_bytes = max_bytes
    async def dispatch(self, request: Request, call_next):
        received = 0
        body = bytearray()
        async for chunk in request.stream():
            received += len(chunk)
            if received > self.max_bytes:
                lang = choose_language(request)
                title = translate(lang, "payload_too_large")
                detail = (
                    f"Payload size {received} exceeds limit of {self.max_bytes} bytes"
                )
                problem = {
                    "type": "about:blank",
                    "title": title,
                    "status": 413,
                    "detail": detail,
                    "trace_id": getattr(request.state, "request_id", ""),
                }
                return JSONResponse(
                    problem,
                    status_code=413,
                    media_type="application/problem+json",
                )
            body.extend(chunk)
        request._body = bytes(body)
        return await call_next(request)
