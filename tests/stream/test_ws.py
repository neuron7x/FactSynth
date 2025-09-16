import pytest
from fastapi.testclient import TestClient

from facts import FactPipelineError
from factsynth_ultimate.api import routers
from factsynth_ultimate.api.v1 import generate
from factsynth_ultimate.app import create_app

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


class StubPipeline:
    def __init__(self, responses: list[str | Exception] | None = None) -> None:
        self._responses = responses or []
        self.calls = 0
        self.queries: list[str] = []

    def run(self, query: str) -> str:
        self.calls += 1
        self.queries.append(query)
        if self.calls <= len(self._responses):
            value = self._responses[self.calls - 1]
            if isinstance(value, Exception):
                raise value
            return value
        return self._responses[-1] if self._responses else ""


def collect_chunks(ws) -> tuple[list[dict], dict]:
    messages: list[dict] = []
    while True:
        message = ws.receive_json()
        messages.append(message)
        if message.get("event") == "end" or message.get("event") == "error":
            break
    end_event = messages[-1]
    chunk_messages = [msg for msg in messages if msg.get("event") == "chunk"]
    return chunk_messages, end_event


def test_ws_stream_chunks():
    pipeline = StubPipeline(["alpha beta gamma delta epsilon"])

    app = create_app()
    app.dependency_overrides[routers.get_fact_pipeline] = lambda: pipeline
    app.dependency_overrides[generate.get_fact_pipeline] = lambda: pipeline
    with (
        TestClient(app) as client,
        client.websocket_connect("/ws/stream", headers={"x-api-key": "change-me"}) as ws,
    ):
        ws.send_json({"text": "alpha beta gamma delta epsilon", "chunk_size": 6})
        start = ws.receive_json()
        assert start == {"event": "start", "cursor": 0, "replay": False}
        chunks, end = collect_chunks(ws)

    chunk_texts = [chunk["text"] for chunk in chunks]
    assert len(chunk_texts) >= 3
    assert end == {"event": "end", "cursor": len(chunk_texts), "replay": False}
    assert pipeline.calls == 1


def test_ws_stream_resume():
    query = "alpha beta gamma delta epsilon"
    pipeline = StubPipeline([query, query])

    app = create_app()
    app.dependency_overrides[routers.get_fact_pipeline] = lambda: pipeline
    app.dependency_overrides[generate.get_fact_pipeline] = lambda: pipeline
    with (
        TestClient(app) as client,
        client.websocket_connect("/ws/stream", headers={"x-api-key": "change-me"}) as ws,
    ):
        ws.send_json({"text": query, "chunk_size": 6})
        ws.receive_json()  # start
        full_chunks, full_end = collect_chunks(ws)

        assert full_end["cursor"] == len(full_chunks)

        resume_index = full_chunks[1]["id"]
        ws.send_json({"text": query, "chunk_size": 6, "cursor": resume_index + 1})
        resume_start = ws.receive_json()
        assert resume_start == {
            "event": "start",
            "cursor": resume_index + 1,
            "replay": True,
        }
        resumed_chunks, resumed_end = collect_chunks(ws)

    expected_texts = [chunk["text"] for chunk in full_chunks][resume_index + 1 :]
    assert [chunk["text"] for chunk in resumed_chunks] == expected_texts
    assert all(chunk["replay"] is True for chunk in resumed_chunks)
    assert resumed_end == {
        "event": "end",
        "cursor": resume_index + 1 + len(resumed_chunks),
        "replay": True,
    }
    expected_calls = 2
    assert pipeline.calls == expected_calls


def test_ws_stream_error_recovery():
    pipeline = StubPipeline([FactPipelineError("temporary"), "alpha beta"])

    app = create_app()
    app.dependency_overrides[routers.get_fact_pipeline] = lambda: pipeline
    app.dependency_overrides[generate.get_fact_pipeline] = lambda: pipeline
    with (
        TestClient(app) as client,
        client.websocket_connect("/ws/stream", headers={"x-api-key": "change-me"}) as ws,
    ):
        ws.send_json({"text": "alpha", "chunk_size": 5})
        start = ws.receive_json()
        assert start == {"event": "start", "cursor": 0, "replay": False}
        error = ws.receive_json()
        assert error == {"event": "error", "message": "temporary", "replay": False}

        ws.send_json({"text": "alpha", "chunk_size": 5})
        ws.receive_json()  # start
        chunks, end = collect_chunks(ws)

    assert [chunk["text"] for chunk in chunks]
    assert end == {"event": "end", "cursor": len(chunks), "replay": False}
    expected_calls = 2
    assert pipeline.calls == expected_calls
