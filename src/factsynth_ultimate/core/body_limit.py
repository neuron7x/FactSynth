"""Request body size limiting middleware."""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from ..i18n import choose_language, translate


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose body exceeds ``max_bytes``."""

    def __init__(self, app: ASGIApp, max_bytes: int = 2_000_000) -> None:
        """Configure the middleware with a byte limit."""

        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Stream the request body and enforce the size limit."""

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
