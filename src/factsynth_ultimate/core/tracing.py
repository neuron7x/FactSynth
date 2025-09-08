from __future__ import annotations

import logging
from contextlib import suppress

log = logging.getLogger("factsynth.telemetry")

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:  # pragma: no cover - optional dependency
    FastAPIInstrumentor = None


def try_enable_otel(app) -> None:
    if FastAPIInstrumentor is None:
        log.info("otel_disabled: missing dependency")
        return
    with suppress(Exception):
        FastAPIInstrumentor.instrument_app(app)
        log.info("otel_enabled")
