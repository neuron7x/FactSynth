"""Middleware providing a request ID for tracing."""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Return the current request ID, if any."""

    return _request_id_ctx.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique ID to each request and response."""

    def __init__(self, app: ASGIApp, header_name: str = "x-request-id") -> None:
        """Configure the header name used for request IDs."""

        super().__init__(app)
        self.header_name = header_name

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Store and propagate a request identifier."""

        rid = request.headers.get(self.header_name) or str(uuid.uuid4())
        request.state.request_id = rid
        _request_id_ctx.set(rid)
        response = await call_next(request)
        response.headers.setdefault(self.header_name, rid)
        return response
