"""High-level orchestration primitives for fact synthesis."""

from .pipeline import (
    FactPipeline,
    FactPipelineError,
    EmptyQueryError,
    NoFactsFoundError,
    AggregationError,
    SearchError,
)

__all__ = [
    "FactPipeline",
    "FactPipelineError",
    "EmptyQueryError",
    "NoFactsFoundError",
    "AggregationError",
    "SearchError",
]
