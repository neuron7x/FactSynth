import asyncio
import logging

import pytest
from pydantic import BaseModel

from factsynth_ultimate.api import verify as verify_mod
from factsynth_ultimate.services.evaluator import evaluate_claim
from factsynth_ultimate.services.retrievers.base import RetrievedDoc

SCORING_RESULT = 0.5
DIVERSITY_RESULT = 0.1


pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_evaluate_claim_composes_and_closes():
    class DummyRetriever:
        def __init__(self):
            self.closed = False

        def search(self, q):
            return [RetrievedDoc(id=q, text=q, score=1.0)]

        def close(self):
            self.closed = True

    retriever = DummyRetriever()

    result = evaluate_claim(
        "alpha",
        policy_check=lambda _: {"allowed": True},
        scoring=lambda _: SCORING_RESULT,
        diversity=lambda _: DIVERSITY_RESULT,
        nli=lambda _: {"label": "neutral"},
        retriever=retriever,
    )

    assert result["policy"] == {"allowed": True}
    assert result["score"] == SCORING_RESULT
    assert result["diversity"] == DIVERSITY_RESULT
    assert result["nli"] == {"label": "neutral"}
    assert result["evidence"][0]["source"] == "alpha"
    assert result["evidence"][0]["content"] == "alpha"
    assert result["evidence"][0]["source_id"]
    assert retriever.closed


def test_evaluate_claim_handles_retriever_exception_and_closes():
    class DummyRetriever:
        def __init__(self):
            self.closed = False

        def search(self, _):
            raise RuntimeError("boom")

        def close(self):
            self.closed = True

    retriever = DummyRetriever()

    result = evaluate_claim("alpha", retriever=retriever)

    assert result["evidence"] == []
    assert retriever.closed


@pytest.mark.asyncio
async def test_evaluate_claim_closes_async_retriever():
    class DummyRetriever:
        def __init__(self):
            self.closed = False

        def search(self, _):
            return []

        async def aclose(self):
            self.closed = True

    retriever = DummyRetriever()

    result = evaluate_claim("gamma", retriever=retriever)
    await asyncio.sleep(0)

    assert result["evidence"] == []
    assert retriever.closed


@pytest.mark.asyncio
async def test_evaluate_claim_handles_async_retriever_exception_and_closes():
    class DummyRetriever:
        def __init__(self):
            self.closed = False

        def search(self, _):
            raise RuntimeError("boom")

        async def aclose(self):
            self.closed = True

    retriever = DummyRetriever()

    result = evaluate_claim("delta", retriever=retriever)
    await asyncio.sleep(0)

    assert result["evidence"] == []
    assert retriever.closed


def test_evaluate_claim_logs_retriever_exception(caplog):
    class DummyRetriever:
        def search(self, _):
            raise RuntimeError("boom")

        def close(self):  # pragma: no cover - no-op
            pass

    with caplog.at_level(logging.ERROR):
        evaluate_claim("beta", retriever=DummyRetriever())

    record = next(r for r in caplog.records if r.message == "retriever_search_error")
    assert record.claim == "beta"
    assert "boom" in record.error


def test_evaluate_claim_loads_retriever_via_entrypoint(monkeypatch):
    from importlib import metadata

    ep = metadata.EntryPoint(
        name="fixture",
        value="factsynth_ultimate.services.retrievers.local:create_fixture_retriever",
        group="factsynth_ultimate.retrievers",
    )

    def fake_entry_points():
        if hasattr(metadata, "EntryPoints"):
            return metadata.EntryPoints([ep])
        return {"factsynth_ultimate.retrievers": [ep]}

    monkeypatch.setattr(metadata, "entry_points", fake_entry_points)

    result = evaluate_claim("alpha", retriever="fixture")
    assert result["evidence"]
    assert result["evidence"][0]["source"] == "default"


def test_verify_exposes_models():
    assert issubclass(verify_mod.FactSynthLock, BaseModel)
    assert issubclass(verify_mod.VerifyRequest, BaseModel)
