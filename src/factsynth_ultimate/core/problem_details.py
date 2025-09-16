"""Utilities for representing RFC 9457 problem details responses."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .tracing import current_trace_id


class ProblemDetails(BaseModel):
    """Representation of an RFC 9457 problem response."""

    title: str
    detail: str
    status: int
    type: str = "about:blank"
    instance: str | None = None
    extras: dict[str, Any] | None = None
    trace_id: str | None = None

    def to_response(self) -> JSONResponse:
        """Return a :class:`JSONResponse` configured for problem+json."""

        payload = self.model_dump(exclude_none=True)
        extras = payload.pop("extras", None)
        if extras:
            payload.update(extras)
        trace_id = payload.get("trace_id") or current_trace_id()
        if trace_id:
            payload["trace_id"] = trace_id
        return JSONResponse(
            payload,
            status_code=self.status,
            media_type="application/problem+json",
        )


def bad_request(title: str, detail: str, **extras: Any) -> ProblemDetails:
    """Convenience helper for constructing a 400 problem response."""

    return ProblemDetails(title=title, detail=detail, status=int(HTTPStatus.BAD_REQUEST), extras=extras)


__all__ = ["ProblemDetails", "bad_request"]
