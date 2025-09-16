# Tracing and Observability

FactSynth Ultimate emits OpenTelemetry traces for critical API paths. This page
describes how to enable exporters, what spans are produced, and how to run the
smoke test that verifies the instrumentation.

## Exporter configuration

Tracing is disabled by default. Enable it by setting the
`FACTSYNTH_TRACE_EXPORTER` environment variable to either `otlp` or `jaeger`
before starting the API server.

```bash
# OTLP over HTTP or gRPC depending on the installed exporter package
export FACTSYNTH_TRACE_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4318"

# Optional service name override (defaults to ``factsynth-ultimate``)
export FACTSYNTH_TRACE_SERVICE_NAME=factsynth-ultimate-prod

# Jaeger agent example
export FACTSYNTH_TRACE_EXPORTER=jaeger
export OTEL_EXPORTER_JAEGER_AGENT_HOST=jaeger-agent
export OTEL_EXPORTER_JAEGER_AGENT_PORT=6831
```

The tracer provider automatically picks up the deployment environment from the
`ENV` variable when it is present. If the required exporter package is missing,
FactSynth logs a warning and continues to run without tracing.

## Manual spans

The application emits explicit spans for the most critical code paths:

- `api.generate` wraps the synchronous fact generation endpoint.
- `api.stream` records Server-Sent Events streaming, including chunk counters.
- `callback.post` tracks background callback delivery attempts.

Each span annotates the current request identifier (if available) and records
retry attempts, chunk sizes, and success/failure metadata. When an error occurs,
the span records the exception and the HTTP status code that is returned to the
client. All error responses now include the active `trace_id` to simplify
cross-referencing log messages with trace exports.

## Smoke test

Run the dedicated test module to validate that spans are produced and enriched
as expected:

```bash
pytest tests/test_tracing_spans.py
```

The smoke test exercises the `/v1/generate` endpoint, the SSE streaming helper,
and the callback retry loop with a fake tracer. It asserts that spans are
created and that trace identifiers surface in problem responses.
