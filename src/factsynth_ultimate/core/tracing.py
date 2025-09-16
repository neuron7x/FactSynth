"""Optional OpenTelemetry instrumentation."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager, suppress
from typing import Any, Iterable, Iterator, Mapping

from fastapi import FastAPI

log = logging.getLogger("factsynth.telemetry")

try:  # pragma: no cover - optional dependency
    from opentelemetry import trace as otel_trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
except ImportError:  # pragma: no cover - optional dependency
    otel_trace = None
    FastAPIInstrumentor = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None

try:  # pragma: no cover - optional dependency
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # type: ignore[assignment]
        OTLPSpanExporter as GrpcOTLPSpanExporter,
    )
except ImportError:  # pragma: no cover - optional dependency
    GrpcOTLPSpanExporter = None

try:  # pragma: no cover - optional dependency
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore[assignment]
        OTLPSpanExporter as HttpOTLPSpanExporter,
    )
except ImportError:  # pragma: no cover - optional dependency
    HttpOTLPSpanExporter = None

try:  # pragma: no cover - optional dependency
    from opentelemetry.trace.status import Status, StatusCode
except ImportError:  # pragma: no cover - optional dependency
    Status = None
    StatusCode = None


_EXPORTER_READY = False


def _parse_headers(raw: str | None, api_key: str | None) -> dict[str, str] | None:
    if not raw and not api_key:
        return None

    headers: dict[str, str] = {}
    if raw:
        parts = [item.strip() for item in raw.split(",") if item.strip()]
        for part in parts:
            key, sep, value = part.partition("=")
            if sep and key and value:
                headers.setdefault(key.strip(), value.strip())

    if api_key and "x-api-key" not in headers:
        headers["x-api-key"] = api_key

    return headers or None


def _create_exporter(endpoint: str, headers: dict[str, str] | None):
    if GrpcOTLPSpanExporter is not None:
        kwargs: dict[str, Any] = {}
        if headers:
            kwargs["headers"] = tuple(headers.items())
        return GrpcOTLPSpanExporter(**kwargs)
    if HttpOTLPSpanExporter is not None:
        kwargs = {"endpoint": endpoint}
        if headers:
            kwargs["headers"] = headers
        return HttpOTLPSpanExporter(**kwargs)
    return None


def _configure_sdk() -> bool:
    global _EXPORTER_READY

    if _EXPORTER_READY:
        return True
    if any(item is None for item in (otel_trace, Resource, TracerProvider, BatchSpanProcessor)):
        return False

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        log.info("otel_exporter_skipped: missing endpoint")
        return False

    api_key = os.getenv("OTEL_EXPORTER_OTLP_API_KEY")
    raw_headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
    headers = _parse_headers(raw_headers, api_key)

    exporter = _create_exporter(endpoint, headers)
    if exporter is None:
        log.info("otel_exporter_skipped: missing exporter implementation")
        return False

    service_name = os.getenv("OTEL_SERVICE_NAME", "factsynth-ultimate-pro")
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    otel_trace.set_tracer_provider(provider)
    _EXPORTER_READY = True
    log.info("otel_exporter_configured", extra={"endpoint": endpoint})
    return True


def try_enable_otel(app: FastAPI) -> None:
    """Instrument *app* with OpenTelemetry if available."""

    if FastAPIInstrumentor is None:
        log.info("otel_disabled: missing dependency")
        return

    configured = False
    with suppress(Exception):
        configured = _configure_sdk()
    with suppress(Exception):
        FastAPIInstrumentor.instrument_app(app)
        log.info("otel_enabled", extra={"exporter_configured": configured})


def _get_tracer():
    if otel_trace is None:
        return None
    return otel_trace.get_tracer("factsynth")


@contextmanager
def start_span(name: str, **attributes: Any) -> Iterator[Any]:
    tracer = _get_tracer()
    if tracer is None:
        yield None
        return
    with tracer.start_as_current_span(name) as span:  # type: ignore[assignment]
        if attributes:
            set_span_attributes(span, attributes)
        yield span


def set_span_attributes(span: Any, attributes: Mapping[str, Any] | Iterable[tuple[str, Any]]) -> None:
    if span is None:
        return
    if isinstance(attributes, Mapping):
        items = attributes.items()
    elif isinstance(attributes, Iterable):
        items = attributes
    else:
        return
    for key, value in items:
        if value is None:
            continue
        with suppress(Exception):
            span.set_attribute(key, value)


def record_exception(span: Any, exc: BaseException) -> None:
    if span is None:
        return
    with suppress(Exception):
        span.record_exception(exc)
    if Status is not None and StatusCode is not None:
        with suppress(Exception):
            span.set_status(Status(StatusCode.ERROR, str(exc)))


__all__ = [
    "record_exception",
    "set_span_attributes",
    "start_span",
    "try_enable_otel",
]
