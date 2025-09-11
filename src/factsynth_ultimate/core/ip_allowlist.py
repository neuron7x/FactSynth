from __future__ import annotations

import ipaddress

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..i18n import choose_language, translate


class IPAllowlistMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, cidrs: list[str] | None = None, skip: tuple[str, ...] = ("/v1/healthz","/metrics")):
        super().__init__(app)
        self.networks = [ipaddress.ip_network(c.strip(), strict=False) for c in (cidrs or [])]
        self.skip = skip
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(s) for s in self.skip) or not self.networks:
            return await call_next(request)
        ip = request.client.host if request.client else "127.0.0.1"
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            addr = None
        if addr and any(addr in n for n in self.networks):
            return await call_next(request)
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
