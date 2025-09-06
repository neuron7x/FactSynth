from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_content_length: int = 256_000):
        super().__init__(app)
        self.max = max_content_length

    async def dispatch(self, request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > self.max:
            raise StarletteHTTPException(status_code=413, detail="payload_too_large")
        return await call_next(request)
