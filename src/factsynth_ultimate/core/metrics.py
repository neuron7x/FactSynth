from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

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
def metrics_bytes() -> bytes:
    return generate_latest()


def metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST


def current_sse_tokens() -> int:
    """Return the current SSE token count."""
    return int(SSE_TOKENS._value.get())
