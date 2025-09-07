from __future__ import annotations
import ipaddress
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

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
        addr = ipaddress.ip_address(ip)
        if any(addr in n for n in self.networks):
            return await call_next(request)
        return JSONResponse({"type":"about:blank","title":"Forbidden","status":403}, status_code=403, media_type="application/problem+json")
