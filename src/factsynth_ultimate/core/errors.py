"""Problem+JSON helpers and exception handlers."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ..i18n import choose_language, translate

logger = logging.getLogger(__name__)


def problem(
    request: Request,
    *,
    type_: str = "about:blank",
    title: str,
    status: int,
    detail: str | None = None,
) -> dict[str, Any]:
    """Return a Problem+JSON payload."""

    return {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": getattr(request.state, "request_id", ""),
    }


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""

    status = exc.status_code
    title = HTTPStatus(status).phrase
    detail = exc.detail if isinstance(exc.detail, str) else None
    body = problem(request, title=title, status=status, detail=detail)
    return JSONResponse(body, status_code=status, media_type="application/problem+json")


async def validation_exception_handler(
    request: Request, exc: ValidationError | RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""

    status = HTTPStatus.UNPROCESSABLE_ENTITY
    title = status.phrase
    body = problem(request, title=title, status=status, detail=str(exc))
    return JSONResponse(body, status_code=status, media_type="application/problem+json")


async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert uncaught exceptions to Problem+JSON responses."""

    logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
    lang = choose_language(request)
    title = translate(lang, "internal_server_error")
    body = problem(
        request,
        title=title,
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
        detail=str(exc),
    )
    return JSONResponse(
        body,
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        media_type="application/problem+json",
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register standard exception handlers on *app*."""

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)
