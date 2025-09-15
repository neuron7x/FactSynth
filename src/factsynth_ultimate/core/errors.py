"""Error handling utilities."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from ..i18n import choose_language, translate

logger = logging.getLogger(__name__)


def install_handlers(app: FastAPI) -> None:
    """Register a generic exception handler on *app*."""

    @app.exception_handler(Exception)
    async def _exc_handler(request: Request, exc: Exception) -> Response:
        """Convert uncaught exceptions to RFC7807 responses."""

        logger.exception(
            "Unhandled exception on %s: %s",
            request.url.path,
            exc,
            extra={"request_id": getattr(request.state, "request_id", "")},
        )
        lang = choose_language(request)
        title = translate(lang, "internal_server_error")
        problem = {
            "type": "about:blank",
            "title": title,
            "status": 500,
            "detail": str(exc),
            "trace_id": getattr(request.state, "request_id", ""),
        }
        return JSONResponse(problem, status_code=500, media_type="application/problem+json")
