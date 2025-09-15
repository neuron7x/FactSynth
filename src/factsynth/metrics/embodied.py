from __future__ import annotations

import math
import os
import time

from prometheus_client import Counter, Gauge, Histogram

EMBODIED_ON = os.getenv("EMBODIED_METRICS_ENABLED", "true").lower() == "true"

REQ_LATENCY = Histogram(
    "fs_req_latency_seconds", "Request latency", buckets=(0.1, 0.25, 0.5, 1, 2, 4, 8, 16)
)
TOKENS_IN = Histogram(
    "fs_tokens_in", "Prompt tokens", buckets=(64, 128, 256, 512, 1024, 2048, 4096)
)
TOKENS_OUT = Histogram(
    "fs_tokens_out", "Completion tokens", buckets=(64, 128, 256, 512, 1024, 2048, 4096)
)
TOOL_CALLS = Histogram("fs_tool_calls", "Tool calls per req", buckets=(0, 1, 2, 3, 5, 8, 13))
RETRIES = Counter("fs_retries_total", "Automatic retries")
USER_REASKS = Counter("fs_user_reasks_total", "User re-asks")
COG_LOAD = Gauge("fs_cognitive_load", "0..1 synthetic load")
FRUSTRATION = Gauge("fs_frustration", "0..1 synthetic frustration")


def compute_cognitive_load(tokens_in: int, constraints: int, tools: int) -> float:
    z = (tokens_in / 2048) + (constraints / 8) + (tools / 5)
    return max(0.0, min(1.0, 1 - math.exp(-z)))


def compute_frustration(latency: float, retries: int, reasks: int) -> float:
    z = (latency / 4.0) + (retries * 0.5) + (reasks * 0.75)
    return max(0.0, min(1.0, 1 - math.exp(-z)))


class ReqTimer:
    def __enter__(self) -> ReqTimer:
        self.t = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        dt = time.perf_counter() - self.t
        REQ_LATENCY.observe(dt)


def record(  # noqa: PLR0913
    tokens_in: int,
    tokens_out: int,
    tools: int,
    constraints: int,
    retries: int = 0,
    user_reasks: int = 0,
    latency_override: float | None = None,
) -> dict[str, float]:
    if not EMBODIED_ON:
        return {}
    if latency_override is not None:
        REQ_LATENCY.observe(latency_override)
    TOKENS_IN.observe(tokens_in)
    TOKENS_OUT.observe(tokens_out)
    TOOL_CALLS.observe(tools)
    if retries:
        RETRIES.inc(retries)
    if user_reasks:
        USER_REASKS.inc(user_reasks)
    load = compute_cognitive_load(tokens_in, constraints, tools)
    COG_LOAD.set(load)
    frustration = compute_frustration(latency_override or 0, retries, user_reasks)
    FRUSTRATION.set(frustration)
    return {"cognitive_load": load, "frustration": frustration}
