from __future__ import annotations
import logging
log = logging.getLogger("factsynth.telemetry")

def try_enable_otel(app) -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
        log.info("otel_enabled")
    except Exception as e:
        log.info("otel_disabled: %s", e.__class__.__name__)
