import json
from http import HTTPStatus

import pytest
from httpx import ASGITransport, AsyncClient

from facts import FactPipelineError

from factsynth_ultimate.api import routers
from factsynth_ultimate.api.v1 import generate
from factsynth_ultimate.app import create_app

class StubPipeline:
    def __init__(self, output: str, *, error: Exception | None = None) -> None:
        self._output = output
        self._error = error
        self.calls = 0
        self.queries: list[str] = []

    def run(self, query: str) -> str:
        self.calls += 1
        self.queries.append(query)
        if self._error is not None:
            raise self._error
        return self._output

def parse_sse(body: bytes) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for block in body.decode().split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event_type: str | None = None
        event_id: str | None = None
        data_payload = ""
        for line in block.splitlines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("id:"):
                event_id = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data_payload += line.split(":", 1)[1].strip()
        data: object | None = json.loads(data_payload) if data_payload else None
        events.append({"event": event_type, "id": event_id, "data": data})
    return events

@pytest.mark.anyio
async def test_sse_stream_chunks_and_resume(base_headers):
    pipeline = StubPipeline("alpha beta gamma delta epsilon zeta")

    params = {"chunk_size": 6}
    payload = {"text": "stream facts"}

    app = create_app()
    app.dependency_overrides[routers.get_fact_pipeline] = lambda: pipeline
    app.dependency_overrides[generate.get_fact_pipeline] = lambda: pipeline
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "POST",
            "/sse/stream",
            headers=base_headers,
            params=params,
            json=payload,
        ) as resp:
            assert resp.status_code == HTTPStatus.OK
            body = await resp.aread()

        events = parse_sse(body)
        assert [evt["event"] for evt in events[:2]] == ["start", "chunk"]
        chunk_events = [evt for evt in events if evt["event"] == "chunk"]
        assert len(chunk_events) >= 3
        chunk_texts = [evt["data"]["text"] for evt in chunk_events]

        resume_source = next(evt for evt in chunk_events if evt["data"]["id"] == 1)
        resume_id = resume_source["id"]
        assert resume_id is not None
        next_cursor = int(resume_id) + 1

        resume_headers = dict(base_headers)
        resume_headers["Last-Event-ID"] = resume_id

        async with client.stream(
            "POST",
            "/sse/stream",
            headers=resume_headers,
            params=params,
            json=payload,
        ) as resumed:
            assert resumed.status_code == HTTPStatus.OK
            resumed_body = await resumed.aread()

    resumed_events = parse_sse(resumed_body)
    assert resumed_events[0]["event"] == "start"
    assert resumed_events[0]["data"] == {"cursor": next_cursor, "replay": True}
    resumed_chunks = [evt for evt in resumed_events if evt["event"] == "chunk"]
    assert [evt["data"]["text"] for evt in resumed_chunks] == chunk_texts[next_cursor:]
    assert all(evt["data"]["replay"] is True for evt in resumed_chunks)

    assert pipeline.calls == 2

@pytest.mark.anyio
async def test_sse_rate_limiter_invoked(base_headers, monkeypatch):
    pipeline = StubPipeline("one two three four five")

    calls: list[float] = []

    async def fake_sleep(duration: float) -> None:  # pragma: no cover - helper
        calls.append(duration)

    monkeypatch.setattr("factsynth_ultimate.stream.asyncio.sleep", fake_sleep)

    app = create_app()
    app.dependency_overrides[routers.get_fact_pipeline] = lambda: pipeline
    app.dependency_overrides[generate.get_fact_pipeline] = lambda: pipeline
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "POST",
            "/sse/stream",
            headers=base_headers,
            params={"chunk_size": 4, "token_delay": 0.1},
            json={"text": "rate control"},
        ) as resp:
            assert resp.status_code == HTTPStatus.OK
            body = await resp.aread()

    events = parse_sse(body)
    chunk_events = [evt for evt in events if evt["event"] == "chunk"]
    assert len(calls) == max(len(chunk_events) - 1, 0)
    assert all(call == pytest.approx(0.1) for call in calls)

@pytest.mark.anyio
async def test_sse_pipeline_error_event(base_headers, monkeypatch):
    error = FactPipelineError("boom")
    pipeline = StubPipeline("", error=error)

    app = create_app()
    app.dependency_overrides[routers.get_fact_pipeline] = lambda: pipeline
    app.dependency_overrides[generate.get_fact_pipeline] = lambda: pipeline
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "POST",
            "/sse/stream",
            headers=base_headers,
            json={"text": "trigger"},
        ) as resp:
            assert resp.status_code == HTTPStatus.OK
            body = await resp.aread()

    events = parse_sse(body)
    assert events[0]["event"] == "start"
    assert events[1]["event"] == "error"
    assert events[1]["data"] == {"message": "boom", "replay": False}
    assert all(evt["event"] != "chunk" for evt in events)
    assert pipeline.calls == 1
