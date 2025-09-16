"""Integration tests for the fact generation endpoint."""

from __future__ import annotations

from http import HTTPStatus

import pytest

from facts import NoFactsFoundError
from factsynth_ultimate.api.v1.generate import (
    PipelineNotReadyError,
    get_fact_pipeline,
)


pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


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

    async def arun(self, query: str) -> str:
        return self.run(query)


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


class UnavailablePipeline:
    """Pipeline stub that mimics missing optional dependencies."""

    def __init__(self, reason: str = "facts backend missing") -> None:
        self._reason = reason

    def run(self, query: str) -> str:  # pragma: no cover - trivial
        raise PipelineNotReadyError(self._reason)

    async def arun(self, query: str) -> str:
        raise PipelineNotReadyError(self._reason)


@pytest.mark.anyio
async def test_generate_reports_pipeline_unavailable(client, base_headers):
    app = client._transport.app
    app.dependency_overrides[get_fact_pipeline] = lambda: UnavailablePipeline(
        reason="facts dependency not installed"
    )
    try:
        response = await client.post(
            "/v1/generate", headers=base_headers, json={"text": "Kyiv"}
        )
    finally:
        app.dependency_overrides.pop(get_fact_pipeline, None)

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    payload = response.json()
    assert payload["status"] == HTTPStatus.SERVICE_UNAVAILABLE
    assert payload["title"] == "Fact generation unavailable"
    assert payload["detail"] == "facts dependency not installed"


class ShortOutputPipeline:
    """Pipeline stub that returns output failing the length validation."""

    def run(self, query: str) -> str:  # pragma: no cover - trivial
        return "too short"

    async def arun(self, query: str) -> str:
        return self.run(query)


@pytest.mark.anyio
async def test_generate_rejects_short_output(client, base_headers):
    app = client._transport.app
    app.dependency_overrides[get_fact_pipeline] = ShortOutputPipeline
    try:
        response = await client.post(
            "/v1/generate", headers=base_headers, json={"text": "Kyiv"}
        )
    finally:
        app.dependency_overrides.pop(get_fact_pipeline, None)

    assert response.status_code == HTTPStatus.BAD_GATEWAY
    payload = response.json()
    assert payload["status"] == HTTPStatus.BAD_GATEWAY
    assert payload["title"] == "Generated text too short"


class LowEntropyPipeline:
    """Pipeline stub that returns deterministic but low-entropy output."""

    def run(self, query: str) -> str:  # pragma: no cover - trivial
        return "a" * 32

    async def arun(self, query: str) -> str:
        return self.run(query)


@pytest.mark.anyio
async def test_generate_rejects_low_entropy_output(client, base_headers):
    app = client._transport.app
    app.dependency_overrides[get_fact_pipeline] = LowEntropyPipeline
    try:
        response = await client.post(
            "/v1/generate", headers=base_headers, json={"text": "Kyiv"}
        )
    finally:
        app.dependency_overrides.pop(get_fact_pipeline, None)

    assert response.status_code == HTTPStatus.BAD_GATEWAY
    payload = response.json()
    assert payload["status"] == HTTPStatus.BAD_GATEWAY
    assert payload["title"] == "Generated text entropy too low"
