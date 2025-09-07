from __future__ import annotations
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Header-based API key auth."""
    def __init__(self, app, api_key: str, header_name: str = "x-api-key", skip: tuple[str, ...] = ("/v1/healthz","/metrics")):
        super().__init__(app)
        self.api_key = api_key
        self.header_name = header_name
        self.skip = skip

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(s) for s in self.skip):
            return await call_next(request)
        provided = request.headers.get(self.header_name)
        if self.api_key and provided == self.api_key:
            return await call_next(request)
        return JSONResponse({"type":"about:blank","title":"Unauthorized","status":401}, status_code=401, media_type="application/problem+json")
