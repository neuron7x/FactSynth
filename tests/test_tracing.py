import logging

import pytest

from factsynth_ultimate.core import tracing

pytestmark = pytest.mark.httpx_mock(
    assert_all_responses_were_requested=False,
    assert_all_requests_were_expected=False,
)


def test_try_enable_otel_missing(monkeypatch, caplog):
    monkeypatch.setattr(tracing, "FastAPIInstrumentor", None)
    with caplog.at_level(logging.INFO):
        tracing.try_enable_otel(object())
    assert "otel_disabled" in caplog.text


def test_try_enable_otel_enabled(monkeypatch, caplog):
    class DummyInstrumentor:
        @staticmethod
        def instrument_app(app):
            app.called = True

    monkeypatch.setattr(tracing, "FastAPIInstrumentor", DummyInstrumentor)
    app = type("App", (), {})()
    with caplog.at_level(logging.INFO):
        tracing.try_enable_otel(app)
    assert getattr(app, "called", False)
    assert "otel_enabled" in caplog.text


def test_start_span(monkeypatch):
    records = []

    class DummySpan:
        def __init__(self, name):
            self.name = name
            self.attrs: dict[str, str] = {}

        def __enter__(self):
            records.append(self)
            return self

        def __exit__(self, *exc):
            return False

        def set_attribute(self, key, value):
            self.attrs[key] = value

    class DummyTracer:
        def start_as_current_span(self, name, **_):
            return DummySpan(name)

    class DummyTrace:
        def get_tracer(self, _):
            return DummyTracer()

    monkeypatch.setattr(tracing, "trace", DummyTrace())

    with tracing.start_span("demo", foo="bar"):
        pass

    assert records and records[0].name == "demo"
    assert records[0].attrs["foo"] == "bar"
