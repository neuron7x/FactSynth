import logging

from factsynth_ultimate.core import tracing


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
