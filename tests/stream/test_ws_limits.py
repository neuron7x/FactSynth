import contextlib
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from factsynth_ultimate.api import routers
from factsynth_ultimate.api.v1 import generate
from factsynth_ultimate.app import create_app
from factsynth_ultimate.auth import ws as ws_auth


class DummyPipeline:
    def __init__(self, response: str = "echo") -> None:
        self._response = response
        self.calls = 0
        self.queries: list[str] = []

    def run(self, query: str) -> str:
        self.calls += 1
        self.queries.append(query)
        return self._response if self._response else query


def _flush_audit_log() -> list[str]:
    logger = logging.getLogger("factsynth.audit")
    for handler in logger.handlers:
        with contextlib.suppress(Exception):
            handler.flush()
    path = Path("audit.log")
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    return [line for line in content.splitlines() if line.strip()]


def _consume_until_end(ws) -> None:
    start = ws.receive_json()
    assert start["event"] == "start"
    while True:
        message = ws.receive_json()
        if message.get("event") in {"end", "error"}:
            break


@pytest.fixture(autouse=True)
def _clean_audit_log():
    Path("audit.log").unlink(missing_ok=True)
    yield
    Path("audit.log").unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def _reset_ws_registry():
    ws_auth.reset_ws_registry()
    yield
    ws_auth.reset_ws_registry()


def test_ws_scope_contains_authenticated_user():
    user = ws_auth.WebSocketUser(api_key="change-me", organization="qa", status="active")
    ws_auth.set_ws_registry({user.api_key: user})

    pipeline = DummyPipeline("hello world")
    app = create_app()
    app.dependency_overrides[routers.get_fact_pipeline] = lambda: pipeline
    app.dependency_overrides[generate.get_fact_pipeline] = lambda: pipeline

    with (
        TestClient(app) as client,
        client.websocket_connect("/ws/stream", headers={"x-api-key": "change-me"}) as ws,
    ):
        stored = ws.scope.get("user")
        assert stored is user
        ws.send_json({"text": "alpha"})
        _consume_until_end(ws)


def test_ws_rate_limit_triggers_and_logs():
    user = ws_auth.WebSocketUser(api_key="change-me", organization="ops", status="active")
    ws_auth.set_ws_registry({user.api_key: user})

    pipeline = DummyPipeline("alpha beta gamma")
    app = create_app()
    app.dependency_overrides[routers.get_fact_pipeline] = lambda: pipeline
    app.dependency_overrides[generate.get_fact_pipeline] = lambda: pipeline
    app.state.ws_rate_limiter = routers.SessionRateLimiter(limit=1, window=60.0)

    with (
        TestClient(app) as client,
        client.websocket_connect("/ws/stream", headers={"x-api-key": "change-me"}) as ws,
    ):
        ws.send_json({"text": "one"})
        _consume_until_end(ws)
        assert pipeline.calls == 1

        ws.send_json({"text": "two"})
        error = ws.receive_json()
        assert error.get("event") == "error"
        assert error.get("message") == "Rate limit exceeded"
        assert error.get("replay") is False

        with pytest.raises((RuntimeError, WebSocketDisconnect)):
            ws.receive_json()

    entries = _flush_audit_log()
    assert any("ws_connect" in line for line in entries)
    assert any("ws_rate_limit" in line for line in entries)
    assert any("ws_disconnect_rate_limited" in line for line in entries)
