"""Middleware enforcing an IP allowlist."""

from __future__ import annotations

import ipaddress
import logging
from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..i18n import choose_language, translate

logger = logging.getLogger(__name__)


class IPAllowlistMiddleware(BaseHTTPMiddleware):
    """Permit requests only from configured networks."""

    def __init__(
        self,
        app,
        cidrs: list[str] | None = None,
        skip: tuple[str, ...] = ("/v1/healthz", "/metrics"),
    ) -> None:
        """Parse CIDR rules and store skip prefixes."""

        super().__init__(app)
        self.networks = [ipaddress.ip_network(c.strip(), strict=False) for c in (cidrs or [])]
        self.skip = skip

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Check the client IP against the allowlist."""

        path = request.url.path
        if any(path.startswith(s) for s in self.skip):
            return await call_next(request)
        ip = request.client.host if request.client else "127.0.0.1"

        def forbidden() -> JSONResponse:
            lang = choose_language(request)
            title = translate(lang, "forbidden")
            detail = f"IP {ip} not allowed"
            problem = {
                "type": "about:blank",
                "title": title,
                "status": 403,
                "detail": detail,
                "trace_id": getattr(request.state, "request_id", ""),
            }
            return JSONResponse(
                problem,
                status_code=403,
                media_type="application/problem+json",
            )

        if not self.networks:
            logger.warning("IP allowlist empty; blocking request from %s", ip)
            return forbidden()
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            logger.warning("invalid client IP %s", ip)
            logger.warning("Unparseable IP address %s", ip)
            addr = None
        if addr and any(addr in n for n in self.networks):
            return await call_next(request)
        return forbidden()
