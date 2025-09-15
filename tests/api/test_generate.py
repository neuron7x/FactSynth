"""Integration tests for the fact generation endpoint."""

from __future__ import annotations

from http import HTTPStatus

import pytest

from facts import NoFactsFoundError
from factsynth_ultimate.api.v1.generate import get_fact_pipeline


class StubPipeline:
    """Minimal pipeline stub that records queries and returns a preset result."""

    def __init__(self, result: str = "synthesized fact.", error: Exception | None = None) -> None:
        self._result = result
        self._error = error
        self.queries: list[str] = []

    def run(self, query: str) -> str:
        self.queries.append(query)
        if self._error is not None:
            raise self._error
        return self._result


@pytest.mark.anyio
async def test_generate_returns_pipeline_output(client, base_headers):
    pipeline = StubPipeline(result="Curated facts about Kyiv.")
    app = client._transport.app
    app.dependency_overrides[get_fact_pipeline] = lambda: pipeline
    try:
        response = await client.post(
            "/v1/generate", headers=base_headers, json={"text": "Kyiv"}
        )
    finally:
        app.dependency_overrides.pop(get_fact_pipeline, None)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"output": {"text": "Curated facts about Kyiv."}}
    assert pipeline.queries == ["Kyiv"]


@pytest.mark.anyio
async def test_generate_maps_pipeline_error_to_problem_details(client, base_headers):
    pipeline = StubPipeline(error=NoFactsFoundError("no supporting knowledge"))
    app = client._transport.app
    app.dependency_overrides[get_fact_pipeline] = lambda: pipeline
    try:
        response = await client.post(
            "/v1/generate", headers=base_headers, json={"text": "unknown"}
        )
    finally:
        app.dependency_overrides.pop(get_fact_pipeline, None)

    assert response.status_code == HTTPStatus.NOT_FOUND
    payload = response.json()
    assert payload["status"] == HTTPStatus.NOT_FOUND
    assert payload["title"] == "Facts not found"
    assert payload["detail"] == "no supporting knowledge"
    assert payload["type"] == "about:blank"
