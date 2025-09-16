"""Fact generation endpoint wired with the :class:`FactPipeline`."""

from __future__ import annotations

import logging
from functools import lru_cache
from http import HTTPStatus

from fastapi import APIRouter, Depends, Request

from facts import (
    AggregationError,
    EmptyQueryError,
    FactPipeline,
    FactPipelineError,
    NoFactsFoundError,
    SearchError,
)
from factsynth_ultimate.core.audit import audit_event
from factsynth_ultimate.core.problem_details import ProblemDetails
from factsynth_ultimate.schemas.requests import GenerateReq

logger = logging.getLogger(__name__)

router = APIRouter()

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


@router.post("/v1/generate")
def generate(
    req: GenerateReq,
    request: Request,
    pipeline: FactPipeline = Depends(get_fact_pipeline),
) -> dict[str, dict[str, str]]:
    """Produce fact statements for ``req.text`` using the orchestrated pipeline."""

    audit_event("generate", _client_host(request))
    try:
        text = pipeline.run(req.text)
    except EmptyQueryError as exc:
        return _problem(HTTPStatus.BAD_REQUEST, "Invalid query", str(exc)).to_response()
    except NoFactsFoundError as exc:
        return _problem(HTTPStatus.NOT_FOUND, "Facts not found", str(exc)).to_response()
    except SearchError as exc:
        logger.warning("Fact search failed: %s", exc)
        return _problem(HTTPStatus.BAD_GATEWAY, "Search failure", str(exc)).to_response()
    except AggregationError as exc:
        logger.warning("Fact aggregation failed: %s", exc)
        return _problem(HTTPStatus.INTERNAL_SERVER_ERROR, "Aggregation failure", str(exc)).to_response()
    except FactPipelineError as exc:
        logger.warning("Fact pipeline error: %s", exc)
        return _problem(HTTPStatus.INTERNAL_SERVER_ERROR, "Fact pipeline failure", str(exc)).to_response()
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected fact generation error")
        return _problem(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal server error",
            "Failed to generate facts",
        ).to_response()

    return {"output": {"text": text}}


__all__ = ["ProblemDetails", "get_fact_pipeline", "generate", "router"]
