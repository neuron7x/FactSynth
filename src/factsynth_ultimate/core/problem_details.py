"""Utilities for representing RFC 9457 problem details responses."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:  # pragma: no cover - optional dependency
    from opentelemetry import trace as otel_trace
except ImportError:  # pragma: no cover - optional dependency
    otel_trace = None


class ProblemDetails(BaseModel):
    """Representation of an RFC 9457 problem response."""

    title: str
    detail: str
    status: int
    type: str = "about:blank"
    instance: str | None = None
    extras: dict[str, Any] | None = None
    trace_id: str | None = None

    def model_post_init(self, __context: Any) -> None:  # pragma: no cover - simple assignment
        if self.trace_id is None:
            self.trace_id = _current_trace_id()

    def to_response(self) -> JSONResponse:
        """Return a :class:`JSONResponse` configured for problem+json."""

        payload = self.model_dump(exclude_none=True)
        extras = payload.pop("extras", None)
        if extras:
            payload.update(extras)
        return JSONResponse(
            payload,
            status_code=self.status,
            media_type="application/problem+json",
        )


def _current_trace_id() -> str | None:
    if otel_trace is None:
        return None
    span = otel_trace.get_current_span()
    if span is None:
        return None
    context = span.get_span_context()
    if context is None or not getattr(context, "is_valid", False):
        return None
    trace_id = getattr(context, "trace_id", 0)
    if not trace_id:
        return None
    return f"{int(trace_id):032x}"


def bad_request(title: str, detail: str, **extras: Any) -> ProblemDetails:
    """Convenience helper for constructing a 400 problem response."""

    return ProblemDetails(title=title, detail=detail, status=int(HTTPStatus.BAD_REQUEST), extras=extras)


__all__ = ["ProblemDetails", "bad_request"]
