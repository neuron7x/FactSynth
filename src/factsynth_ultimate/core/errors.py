from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..i18n import choose_language, translate

logger = logging.getLogger(__name__)


def install_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def _exc_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
        lang = choose_language(request)
        title = translate(lang, "internal_server_error")
        problem = {"type": "about:blank", "title": title, "status": 500}
        return JSONResponse(problem, status_code=500, media_type="application/problem+json")
