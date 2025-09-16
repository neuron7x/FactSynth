"""Middleware adding security-related HTTP headers."""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp


def _defaults(hsts: bool) -> dict[str, str]:
    """Return a baseline set of headers for secure responses."""

    # Headers based on OWASP Secure Headers recommendations for protecting API responses.
    base = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        # Intentionally omit deprecated X-XSS-Protection header
        "Permissions-Policy": (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        ),
        # API без UI: жорсткий CSP
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    }
    if hsts:
        base["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return base


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply headers that enforce a secure-by-default policy."""

    def __init__(
        self, app: ASGIApp, headers: dict[str, str] | None = None, hsts: bool = False
    ) -> None:
        """Merge custom headers with defaults."""

        super().__init__(app)
        self.headers = {**_defaults(hsts), **(headers or {})}

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Set security headers on outgoing responses."""

        response = await call_next(request)
        for k, v in self.headers.items():
            response.headers.setdefault(k, v)
        return response
