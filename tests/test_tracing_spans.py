"""Smoke tests covering manual tracing spans."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from factsynth_ultimate.api.routers import _post_callback, _sse_stream
from factsynth_ultimate.api.v1.generate import get_fact_pipeline
from factsynth_ultimate.app import create_app
from factsynth_ultimate.core import tracing
from factsynth_ultimate.schemas.requests import ScoreReq


class FakeSpan:
    def __init__(self, name: str, tracer: "FakeTracer", trace_id: str) -> None:
        self.name = name
        self.tracer = tracer
        self.trace_id = trace_id
        self.attributes: dict[str, Any] = {}
        self.events: list[tuple[str, dict[str, Any]]] = []
        self.exceptions: list[BaseException] = []

    def __enter__(self) -> "FakeSpan":
        self.tracer.spans.append(self)
        self.tracer.current_trace_id = self.trace_id
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any) -> bool:
        self.tracer.current_trace_id = None
        return False

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append((name, attributes or {}))

    def record_exception(self, exc: BaseException) -> None:
        self.exceptions.append(exc)


class FakeTracer:
    def __init__(self) -> None:
        self.spans: list[FakeSpan] = []
        self._counter = 0
        self.current_trace_id: str | None = None

    def start_as_current_span(self, name: str, **_: Any) -> FakeSpan:
        self._counter += 1
        trace_id = f"{self._counter:032x}"
        return FakeSpan(name, self, trace_id)


@pytest.fixture()
def fake_tracer(monkeypatch: pytest.MonkeyPatch) -> FakeTracer:
    tracer = FakeTracer()
    monkeypatch.setattr(tracing, "get_tracer", lambda _: tracer)
    monkeypatch.setattr(tracing, "current_trace_id", lambda: tracer.current_trace_id)
    monkeypatch.setattr(
        "factsynth_ultimate.core.problem_details.current_trace_id",
        lambda: tracer.current_trace_id,
    )
    return tracer


def test_generate_span_and_trace_id(monkeypatch: pytest.MonkeyPatch, fake_tracer: FakeTracer) -> None:
    class DummyInstrumentor:
        @staticmethod
        def instrument_app(app: Any) -> None:
            app.instrumented = True

    monkeypatch.setattr(tracing, "FastAPIInstrumentor", DummyInstrumentor)

    class BoomPipeline:
        def run(self, _: str) -> str:  # pragma: no cover - simple stub
            raise ValueError("boom")

    app = create_app()
    app.dependency_overrides[get_fact_pipeline] = lambda: BoomPipeline()

    client = TestClient(app)
    response = client.post(
        "/v1/generate",
        json={"text": "boom"},
        headers={"x-api-key": "change-me"},
    )

    assert response.status_code == 500
    payload = response.json()
    assert payload["trace_id"] == fake_tracer.spans[0].trace_id

    span = fake_tracer.spans[0]
    assert span.name == "api.generate"
    assert span.attributes["generate.outcome"] == "error"
    assert any(isinstance(exc, ValueError) for exc in span.exceptions)


@pytest.mark.asyncio()
async def test_stream_span_records_chunks(fake_tracer: FakeTracer) -> None:
    class DummyPipeline:
        def run(self, text: str) -> str:
            return text

    class DummyState:
        request_id = "stream-req"

    class DummyRequest:
        def __init__(self) -> None:
            self.headers: dict[str, str] = {}
            self.state = DummyState()

        async def is_disconnected(self) -> bool:
            return False

    req = ScoreReq(text="alpha beta gamma delta")
    request = DummyRequest()

    response = await _sse_stream(
        req,
        request,
        DummyPipeline(),
        token_delay=0.0,
        chunk_size=6,
        cursor=None,
    )

    async for _ in response.body_iterator:
        pass

    stream_spans = [span for span in fake_tracer.spans if span.name == "api.stream"]
    assert stream_spans, "stream span was not recorded"
    stream_span = stream_spans[0]
    assert stream_span.attributes["stream.outcome"] == "success"
    assert stream_span.attributes["stream.chunks_sent"] >= 1
    assert any(event[0] == "stream.chunk" for event in stream_span.events)


@pytest.mark.asyncio()
async def test_callback_span_records_attempts(monkeypatch: pytest.MonkeyPatch, fake_tracer: FakeTracer) -> None:
    responses = [
        type("Resp", (), {"status_code": 500})(),
        type("Resp", (), {"status_code": 200})(),
    ]

    class DummyClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
            pass

        async def __aenter__(self) -> "DummyClient":
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            return None

        async def post(self, url: str, json: Any) -> Any:
            _ = url, json
            return responses.pop(0)

    monkeypatch.setattr("factsynth_ultimate.api.routers.httpx.AsyncClient", DummyClient)

    await _post_callback("https://example.com", {"ok": True}, request_id="callback-1")

    callback_spans = [span for span in fake_tracer.spans if span.name == "callback.post"]
    assert callback_spans, "callback span was not recorded"
    span = callback_spans[0]
    assert span.attributes["callback.status"] == "success"
    assert span.attributes["callback.attempts_used"] == 2
    assert any(event[0] == "callback.attempt" for event in span.events)
