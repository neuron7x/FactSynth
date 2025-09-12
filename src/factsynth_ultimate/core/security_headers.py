from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


def _defaults(hsts: bool) -> dict[str, str]:
    # Headers based on OWASP Secure Headers recommendations for protecting API responses.
    base = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=(), interest-cohort=()",
        # API без UI: жорсткий CSP
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    }
    if hsts:
        base["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return base

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, headers: dict[str, str] | None = None, hsts: bool = False):
        super().__init__(app)
        self.headers = {**_defaults(hsts), **(headers or {})}
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for k, v in self.headers.items():
            response.headers.setdefault(k, v)
        return response
