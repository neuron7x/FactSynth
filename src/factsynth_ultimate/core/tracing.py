"""Optional OpenTelemetry instrumentation."""

from __future__ import annotations

import logging
from contextlib import nullcontext, suppress
from typing import Any, Iterator

from fastapi import FastAPI

log = logging.getLogger("factsynth.telemetry")

try:  # pragma: no cover - optional dependency
    from opentelemetry import context as otel_context, trace as otel_trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:  # pragma: no cover - optional dependency
    otel_trace = None
    otel_context = None
    FastAPIInstrumentor = None


class _NoopSpan:  # pragma: no cover - trivial container
    def __enter__(self) -> None:  # noqa: D401 - same semantics as context managers
        return None

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:  # noqa: D401
        return None


class _NoopTracer:  # pragma: no cover - trivial container
    def start_as_current_span(self, *_args: Any, **_kwargs: Any) -> _NoopSpan:
        return _NoopSpan()


class _NoopTrace:  # pragma: no cover - trivial container
    def get_tracer(self, *_args: Any, **_kwargs: Any) -> _NoopTracer:
        return _NoopTracer()


trace = otel_trace if otel_trace is not None else _NoopTrace()
context = otel_context if otel_context is not None else type("_NoopContext", (), {
    "get_current": staticmethod(lambda: None),
    "attach": staticmethod(lambda _ctx: None),
    "detach": staticmethod(lambda _token: None),
})()


def try_enable_otel(app: FastAPI) -> None:
    """Instrument *app* with OpenTelemetry if available."""

    if FastAPIInstrumentor is None:
        log.info("otel_disabled: missing dependency")
        return
    with suppress(Exception):
        FastAPIInstrumentor.instrument_app(app)
        log.info("otel_enabled")


def start_span(name: str, **attributes: Any) -> Iterator[Any]:
    """Return context manager creating a span with ``attributes`` if possible."""

    tracer = trace.get_tracer("factsynth_ultimate")
    cm = tracer.start_as_current_span(name)
    if cm is nullcontext:  # pragma: no cover - defensive
        return cm  # type: ignore[return-value]

    class _Wrapper:
        def __enter__(self) -> Any:
            span = cm.__enter__()
            for key, value in attributes.items():
                try:
                    span.set_attribute(key, value)
                except Exception:  # pragma: no cover - optional attribute support
                    pass
            return span

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            cm.__exit__(exc_type, exc, tb)

    return _Wrapper()


__all__ = ["trace", "context", "try_enable_otel", "start_span"]
