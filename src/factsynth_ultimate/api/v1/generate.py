"""Fact generation endpoint wired with the :class:`FactPipeline`."""

from __future__ import annotations

import logging
import math
from collections import Counter
from functools import lru_cache
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from factsynth_ultimate.core import tracing
from factsynth_ultimate.core.audit import audit_event
from factsynth_ultimate.core.problem_details import ProblemDetails
from factsynth_ultimate.schemas.requests import GenerateReq

try:  # pragma: no cover - exercised indirectly when optional dependency is missing
    from facts import (
        AggregationError,
        EmptyQueryError,
        FactPipeline,
        FactPipelineError,
        NoFactsFoundError,
        SearchError,
    )
except ModuleNotFoundError:  # pragma: no cover - optional dependency guard
    class FactPipelineError(RuntimeError):  # type: ignore[no-redef]
        """Fallback base error when the optional ``facts`` package is missing."""


    class EmptyQueryError(FactPipelineError):  # type: ignore[no-redef]
        """Raised when the incoming query is blank."""


    class SearchError(FactPipelineError):  # type: ignore[no-redef]
        """Raised when the retrieval layer fails."""


    class NoFactsFoundError(SearchError):  # type: ignore[no-redef]
        """Raised when no supporting knowledge can be located."""


    class AggregationError(FactPipelineError):  # type: ignore[no-redef]
        """Raised when the aggregation/formatting stage produces invalid output."""


    class FactPipeline:  # type: ignore[no-redef]
        """Minimal pipeline stub used when the real implementation is unavailable."""

        _reason = "facts package is not installed"

        def run(self, query: str) -> str:
            raise PipelineNotReadyError(self._reason)


PIPELINE_MIN_LEN = 16
PIPELINE_MAX_LEN = 10_000
PIPELINE_MIN_ENTROPY = 0.4
PIPELINE_MAX_ENTROPY = 6.5


class PipelineNotReadyError(FactPipelineError):
    """Raised when the fact pipeline cannot satisfy a generation request."""

    def __init__(self, reason: str | None = None) -> None:
        self.reason = reason or "Fact pipeline is not available"
        super().__init__(self.reason)


logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()

def _client_host(request: Request) -> str:
    """Best-effort retrieval of the requesting client's host."""

    return getattr(getattr(request, "client", None), "host", "unknown")


@lru_cache(maxsize=1)
def _pipeline_singleton() -> FactPipeline:
    """Return a singleton :class:`FactPipeline` instance."""

    return FactPipeline()


def get_fact_pipeline() -> FactPipeline:
    """FastAPI dependency returning the shared :class:`FactPipeline`."""

    return _pipeline_singleton()


def _problem(status: HTTPStatus, title: str, detail: str) -> ProblemDetails:
    return ProblemDetails(title=title, detail=detail, status=int(status))


def _entropy_bits_per_char(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    total = len(text)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _validate_generated_text(text: str) -> ProblemDetails | None:
    trimmed = text.strip()
    if not trimmed:
        return _problem(
            HTTPStatus.BAD_GATEWAY,
            "Invalid generation output",
            "Pipeline returned an empty result",
        )

    length = len(trimmed)
    if length < PIPELINE_MIN_LEN:
        return _problem(
            HTTPStatus.BAD_GATEWAY,
            "Generated text too short",
            f"Received {length} characters but require at least {PIPELINE_MIN_LEN}",
        )

    if length > PIPELINE_MAX_LEN:
        return _problem(
            HTTPStatus.BAD_GATEWAY,
            "Generated text too long",
            f"Received {length} characters but the maximum is {PIPELINE_MAX_LEN}",
        )

    entropy = _entropy_bits_per_char(trimmed)
    if entropy < PIPELINE_MIN_ENTROPY:
        return _problem(
            HTTPStatus.BAD_GATEWAY,
            "Generated text entropy too low",
            f"Entropy {entropy:.2f} bits/char below minimum {PIPELINE_MIN_ENTROPY}",
        )

    if entropy > PIPELINE_MAX_ENTROPY:
        return _problem(
            HTTPStatus.BAD_GATEWAY,
            "Generated text entropy too high",
            f"Entropy {entropy:.2f} bits/char above maximum {PIPELINE_MAX_ENTROPY}",
        )

    return None


def _record_generate_failure(span: Any, status: HTTPStatus, exc: Exception | None = None) -> None:
    if hasattr(span, "set_attribute"):
        span.set_attribute("generate.status_code", int(status))
        span.set_attribute("generate.outcome", "error")
        if exc is not None:
            span.set_attribute("generate.error.type", exc.__class__.__name__)
    if exc is not None and hasattr(span, "record_exception"):
        span.record_exception(exc)


@router.post("/v1/generate")
def generate(
    req: GenerateReq,
    request: Request,
    pipeline: FactPipeline = Depends(get_fact_pipeline),
) -> JSONResponse | dict[str, dict[str, str]]:
    """Produce fact statements for ``req.text`` using the orchestrated pipeline."""

    tracer = tracing.get_tracer(__name__)
    state = getattr(request, "state", None)
    request_id = getattr(state, "request_id", "")
    with tracer.start_as_current_span("api.generate") as span:
        if hasattr(span, "set_attribute"):
            span.set_attribute("app.request_id", request_id)
            span.set_attribute("generate.request.length", len(req.text))
            span.set_attribute("generate.pipeline", type(pipeline).__name__)

        audit_event("generate", _client_host(request))
        try:
            text = pipeline.run(req.text)
        except PipelineNotReadyError as exc:
            logger.warning("Fact pipeline unavailable: %s", exc.reason)
            _record_generate_failure(span, HTTPStatus.SERVICE_UNAVAILABLE, exc)
            return _problem(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "Fact generation unavailable",
                exc.reason,
            ).to_response()
        except EmptyQueryError as exc:
            _record_generate_failure(span, HTTPStatus.BAD_REQUEST, exc)
            return _problem(HTTPStatus.BAD_REQUEST, "Invalid query", str(exc)).to_response()
        except NoFactsFoundError as exc:
            _record_generate_failure(span, HTTPStatus.NOT_FOUND, exc)
            return _problem(HTTPStatus.NOT_FOUND, "Facts not found", str(exc)).to_response()
        except SearchError as exc:
            logger.warning("Fact search failed: %s", exc)
            _record_generate_failure(span, HTTPStatus.BAD_GATEWAY, exc)
            return _problem(HTTPStatus.BAD_GATEWAY, "Search failure", str(exc)).to_response()
        except AggregationError as exc:
            logger.warning("Fact aggregation failed: %s", exc)
            _record_generate_failure(span, HTTPStatus.INTERNAL_SERVER_ERROR, exc)
            return _problem(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Aggregation failure",
                str(exc),
            ).to_response()
        except FactPipelineError as exc:
            logger.warning("Fact pipeline error: %s", exc)
            _record_generate_failure(span, HTTPStatus.INTERNAL_SERVER_ERROR, exc)
            return _problem(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Fact pipeline failure",
                str(exc),
            ).to_response()
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected fact generation error")
            _record_generate_failure(span, HTTPStatus.INTERNAL_SERVER_ERROR, exc)
            return _problem(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Internal server error",
                "Failed to generate facts",
            ).to_response()

        if problem := _validate_generated_text(text):
            logger.warning("Rejected pipeline output: %s", problem.detail)
            if hasattr(span, "set_attribute"):
                span.set_attribute("generate.outcome", "rejected")
                span.set_attribute("generate.status_code", problem.status)
            return problem.to_response()

        if hasattr(span, "set_attribute"):
            span.set_attribute("generate.status_code", int(HTTPStatus.OK))
            span.set_attribute("generate.outcome", "success")
            span.set_attribute("generate.output.length", len(text))

        return {"output": {"text": text}}


__all__ = ["ProblemDetails", "PipelineNotReadyError", "get_fact_pipeline", "generate", "router"]
