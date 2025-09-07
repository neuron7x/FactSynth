from __future__ import annotations
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

REQUESTS = Counter(
    "factsynth_requests_total",
    "Total HTTP requests",
    labelnames=("method","route","status")
)
LATENCY = Histogram(
    "factsynth_request_latency_seconds",
    "Request latency in seconds",
    labelnames=("route",)
)
UP = Gauge("factsynth_up", "1 if the service is up")
UP.set(1)

def metrics_bytes() -> bytes:
    return generate_latest()

def metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST
