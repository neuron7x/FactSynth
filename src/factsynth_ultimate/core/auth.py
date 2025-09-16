"""Middleware implementing simple header-based API key authentication."""

from __future__ import annotations

import hmac
import logging
import re
from collections.abc import Awaitable, Callable, Iterable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from ..i18n import choose_language, translate

logger = logging.getLogger(__name__)


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Header-based API key auth."""

    def __init__(
        self,
        app: ASGIApp,
        api_keys: Iterable[str] | str,
        header_name: str = "x-api-key",
        skip: Iterable[str] = ("/v1/healthz", "/metrics"),
    ) -> None:
        """Store configuration for later request checks."""

        super().__init__(app)
        if isinstance(api_keys, str):
            api_keys = [api_keys]
        self.api_keys = {key.casefold() for key in api_keys}
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
        if not self.api_keys:
            return await call_next(request)

        if provided is None:
            return self._reject(request, 401, "Missing API key", "unauthorized")

        provided_bytes = provided.casefold().encode()
        for key in self.api_keys:
            if hmac.compare_digest(provided_bytes, key.encode()):
                return await call_next(request)

        return self._reject(request, 403, "Invalid API key", "forbidden")

    @staticmethod
    def _reject(request: Request, status: int, detail: str, title_key: str) -> JSONResponse:
        """Log failed auth and return an RFC 9457 problem response."""

        client_id = request.headers.get("x-client-id", "")
        request_id = getattr(request.state, "request_id", "")
        logger.warning("auth failed", extra={"client_id": client_id})

        lang = choose_language(request)
        problem = {
            "type": "about:blank",
            "title": translate(lang, title_key),
            "status": status,
            "detail": detail,
            "trace_id": request_id,
        }
        return JSONResponse(problem, status_code=status, media_type="application/problem+json")
