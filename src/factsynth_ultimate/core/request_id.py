from __future__ import annotations

import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, header_name: str = "x-request-id"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get(self.header_name) or str(uuid.uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        response.headers.setdefault(self.header_name, rid)
        return response
