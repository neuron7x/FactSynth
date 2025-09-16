"""OpenTelemetry helpers and instrumentation glue."""

from __future__ import annotations

import logging
import os
from contextlib import suppress
from importlib import import_module
from typing import Any, Callable

from fastapi import FastAPI

log = logging.getLogger("factsynth.telemetry")

try:  # pragma: no cover - optional dependency
    from opentelemetry import trace as _otel_trace  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    _otel_trace = None

try:  # pragma: no cover - optional dependency
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    FastAPIInstrumentor = None


_EXPORTER_ENV = "FACTSYNTH_TRACE_EXPORTER"
_SERVICE_NAME_ENV = "FACTSYNTH_TRACE_SERVICE_NAME"
_DEFAULT_SERVICE_NAME = "factsynth-ultimate"


class _NoOpSpan:
    """Fallback span implementation when OpenTelemetry is unavailable."""

    def __enter__(self) -> "_NoOpSpan":  # pragma: no cover - trivial
        return self

    def __exit__(self, *exc: object) -> bool:  # pragma: no cover - trivial
        return False

    # The real span API exposes these methods; we provide graceful no-ops.
    def set_attribute(self, *_args: object, **_kwargs: object) -> None:
        return None

    def add_event(self, *_args: object, **_kwargs: object) -> None:
        return None

    def record_exception(self, *_args: object, **_kwargs: object) -> None:
        return None

    def set_status(self, *_args: object, **_kwargs: object) -> None:
        return None


class _NoOpTracer:
    """Tracer shim yielding :class:`_NoOpSpan` instances."""

    def start_as_current_span(self, *_args: object, **_kwargs: object) -> _NoOpSpan:
        return _NoOpSpan()


_tracer_factory: Callable[[str], Any] | None = None
_provider_configured = False


def _default_tracer_factory(component: str) -> Any:
    if _otel_trace is None:  # pragma: no cover - optional dependency path
        return _NoOpTracer()
    return _otel_trace.get_tracer(component)


def set_tracer_factory(factory: Callable[[str], Any]) -> None:
    """Override the tracer factory (intended for tests)."""

    global _tracer_factory
    _tracer_factory = factory


def get_tracer(component: str) -> Any:
    """Return a tracer object for ``component``.

    The returned object follows the OpenTelemetry ``Tracer`` protocol. If
    OpenTelemetry is unavailable, a lightweight no-op tracer is returned so
    callers can safely use ``start_as_current_span``.
    """

    factory = _tracer_factory or _default_tracer_factory
    try:
        return factory(component)
    except Exception:  # pragma: no cover - defensive
        log.debug("failed to acquire tracer", exc_info=True)
        return _NoOpTracer()


def current_trace_id() -> str | None:
    """Return the current trace identifier, if available."""

    if _otel_trace is None:  # pragma: no cover - optional dependency path
        return None
    span = _otel_trace.get_current_span()
    if span is None:
        return None
    ctx = getattr(span, "get_span_context", lambda: None)()
    trace_id = getattr(ctx, "trace_id", 0)
    is_valid = getattr(ctx, "is_valid", lambda: False)()
    if not is_valid:
        return None
    return f"{trace_id:032x}"


def _batch_span_processor() -> Any | None:
    try:
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
    except ImportError:  # pragma: no cover - optional dependency
        return None
    return BatchSpanProcessor


def _resource_factory() -> tuple[Any | None, str]:
    try:
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource  # type: ignore
    except ImportError:  # pragma: no cover - optional dependency
        return None, "service.name"
    return Resource, SERVICE_NAME


def _load_otlp_exporter() -> Any | None:
    modules = (
        "opentelemetry.exporter.otlp.proto.http.trace_exporter",
        "opentelemetry.exporter.otlp.proto.grpc.trace_exporter",
    )
    for module_path in modules:
        with suppress(ImportError, AttributeError):
            module = import_module(module_path)
            exporter_cls = getattr(module, "OTLPSpanExporter")
            return exporter_cls()  # type: ignore[no-any-return]
    log.warning("otel_exporter_unavailable", extra={"exporter": "otlp"})
    return None


def _load_jaeger_exporter() -> Any | None:
    with suppress(ImportError):
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter  # type: ignore
    if "JaegerExporter" not in locals():  # pragma: no cover - optional dependency
        log.warning("otel_exporter_unavailable", extra={"exporter": "jaeger"})
        return None

    kwargs: dict[str, Any] = {}
    endpoint = os.getenv("OTEL_EXPORTER_JAEGER_ENDPOINT")
    host = os.getenv("OTEL_EXPORTER_JAEGER_AGENT_HOST")
    port = os.getenv("OTEL_EXPORTER_JAEGER_AGENT_PORT")

    if endpoint:
        kwargs["collector_endpoint"] = endpoint
        if username := os.getenv("OTEL_EXPORTER_JAEGER_USER"):
            kwargs["username"] = username
        if password := os.getenv("OTEL_EXPORTER_JAEGER_PASSWORD"):
            kwargs["password"] = password
        if certificate := os.getenv("OTEL_EXPORTER_JAEGER_CERTIFICATE"):
            kwargs["certificate"] = certificate
        insecure_raw = os.getenv("OTEL_EXPORTER_JAEGER_INSECURE")
        if insecure_raw:
            kwargs["insecure"] = insecure_raw.lower() in {"1", "true", "yes", "on"}
    else:
        if host:
            kwargs["agent_host_name"] = host
        if port:
            with suppress(ValueError):
                kwargs["agent_port"] = int(port)

    return JaegerExporter(**kwargs)


def _select_exporter() -> tuple[Any | None, str | None]:
    name = os.getenv(_EXPORTER_ENV, "").strip().lower()
    if not name:
        log.info("otel_exporter_skipped: not configured")
        return None, None
    if name == "otlp":
        return _load_otlp_exporter(), name
    if name == "jaeger":
        return _load_jaeger_exporter(), name
    log.warning("otel_exporter_unknown", extra={"exporter": name})
    return None, name


def _configure_provider() -> None:
    global _provider_configured
    if _provider_configured:
        return
    if _otel_trace is None:  # pragma: no cover - optional dependency path
        log.debug("OpenTelemetry trace API unavailable; skipping provider setup")
        return

    exporter, exporter_name = _select_exporter()
    if exporter is None:
        if exporter_name:
            log.warning("otel_exporter_not_initialized", extra={"exporter": exporter_name})
        return

    BatchSpanProcessor = _batch_span_processor()
    resource_factory, service_name_attr = _resource_factory()
    try:
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    except ImportError:  # pragma: no cover - optional dependency
        log.warning("otel_sdk_missing")
        return
    if BatchSpanProcessor is None or resource_factory is None:
        log.warning("otel_sdk_incomplete")
        return

    service_name = (
        os.getenv("OTEL_SERVICE_NAME")
        or os.getenv(_SERVICE_NAME_ENV)
        or _DEFAULT_SERVICE_NAME
    )
    resource_attributes = {service_name_attr: service_name}
    if env := os.getenv("ENV"):
        resource_attributes["deployment.environment"] = env

    provider = TracerProvider(resource=resource_factory.create(resource_attributes))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    _otel_trace.set_tracer_provider(provider)
    _provider_configured = True
    log.info("otel_exporter_configured", extra={"exporter": exporter_name, "service": service_name})


def try_enable_otel(app: FastAPI) -> None:
    """Instrument *app* with OpenTelemetry if the dependency is available."""

    if FastAPIInstrumentor is None:
        log.info("otel_disabled: missing dependency")
        return

    _configure_provider()

    with suppress(Exception):
        FastAPIInstrumentor.instrument_app(app)
        log.info("otel_enabled")


__all__ = [
    "FastAPIInstrumentor",
    "current_trace_id",
    "get_tracer",
    "set_tracer_factory",
    "try_enable_otel",
]

