from __future__ import annotations
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Simple header-based API key auth.

    - Looks for header: `x-api-key`
    - Skips: `/v1/healthz`, `/metrics`
    """
    def __init__(self, app, api_key: str, header_name: str = "x-api-key"):
        super().__init__(app)
        self.api_key = api_key
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith(("/v1/healthz", "/metrics")):
            return await call_next(request)
        provided = request.headers.get(self.header_name)
        if not provided or provided != self.api_key:
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)
