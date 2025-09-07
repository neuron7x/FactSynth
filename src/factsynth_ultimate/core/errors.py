from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

PROBLEM = {"type":"about:blank","title":"Internal Server Error","status":500}

def install_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def _exc_handler(request: Request, exc: Exception):
        return JSONResponse(PROBLEM, status_code=500, media_type="application/problem+json")
