from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

PROBLEM = {"type":"about:blank","title":"Internal Server Error","status":500}

def install_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def _exc_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
        return JSONResponse(PROBLEM, status_code=500, media_type="application/problem+json")
