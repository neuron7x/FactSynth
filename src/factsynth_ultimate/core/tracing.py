from __future__ import annotations

import logging
import os
from contextlib import suppress

log = logging.getLogger("factsynth.telemetry")

try:  # optional dependencies
    from opentelemetry import metrics, trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter,
    )
except Exception:  # pragma: no cover - missing deps
    FastAPIInstrumentor = None


def try_enable_otel(app) -> None:
    if FastAPIInstrumentor is None:
        log.info("otel_disabled: missing dependency")
        return
    with suppress(Exception):
        service_name = os.getenv("OTEL_SERVICE_NAME", "factsynth")
        resource = Resource.create({"service.name": service_name})

        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(tracer_provider)

        reader = PeriodicExportingMetricReader(OTLPMetricExporter())
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(meter_provider)

        FastAPIInstrumentor.instrument_app(app)
        log.info("otel_enabled")
