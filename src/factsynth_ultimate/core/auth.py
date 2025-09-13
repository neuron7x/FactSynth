"""Middleware implementing simple header-based API key authentication."""

from __future__ import annotations

import re
from typing import Awaitable, Callable, Iterable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..i18n import choose_language, translate
from .errors import problem


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Header-based API key auth."""

    def __init__(
        self,
        app,
        api_key: str,
        header_name: str = "x-api-key",
        skip: Iterable[str] = ("/v1/healthz", "/metrics"),
    ) -> None:
        """Store configuration for later request checks."""

        super().__init__(app)
        self.api_key = api_key
        self.header_name = header_name
        self.skip_exact: set[str] = set()
        patterns = []
        for s in skip:
            if s.startswith("^") and s.endswith("$"):
                patterns.append(re.compile(s))
            else:
                self.skip_exact.add(s)
        self.skip_patterns = tuple(patterns)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Check the API key header before processing the request."""

        path = request.url.path
        if path in self.skip_exact or any(p.fullmatch(path) for p in self.skip_patterns):
            return await call_next(request)
        provided = request.headers.get(self.header_name)
        if self.api_key and provided == self.api_key:
            return await call_next(request)
        lang = choose_language(request)
        title = translate(lang, "unauthorized")
        detail = "Invalid or missing API key"
        body = problem(
            request,
            title=title,
            status=401,
            detail=detail,
        )
        return JSONResponse(
            body,
            status_code=401,
            media_type="application/problem+json",
        )
