"""Prometheus metrics helpers."""

from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

REQUESTS = Counter(
    "factsynth_requests_total",
    "Total HTTP requests",
    ("method", "route", "status"),
)
LATENCY = Histogram(
    "factsynth_request_latency_seconds",
    "Request latency seconds",
    ("route",),
)
UP = Gauge("factsynth_up", "1 if service up")
UP.set(1)

SCORING_TIME = Histogram("factsynth_scoring_seconds", "Time to compute score")
SSE_TOKENS = Counter(
    "factsynth_sse_tokens_total",
    "Number of SSE tokens streamed",
)

EXPLANATION_SATISFACTION = Histogram(
    "factsynth_explanation_satisfaction_score",
    "User-rated satisfaction with explanations",
    buckets=(0.0, 0.25, 0.5, 0.75, 1.0),
)
CITATION_PRECISION = Histogram(
    "factsynth_citation_precision",
    "User-perceived citation accuracy",
    buckets=(0.0, 0.25, 0.5, 0.75, 1.0),
)


def metrics_bytes() -> bytes:
    """Return all metrics in Prometheus text format."""

    return generate_latest()


def metrics_content_type() -> str:
    """Return the Content-Type header for :func:`metrics_bytes`."""

    return CONTENT_TYPE_LATEST


def current_sse_tokens() -> int:
    """Return the current SSE token count."""
    return int(SSE_TOKENS._value.get())
