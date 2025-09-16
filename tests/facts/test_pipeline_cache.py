"""Tests for caching behaviour of :class:`FactPipeline`."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from facts.pipeline import FactPipeline
from factsynth_ultimate.services.retrievers.base import RetrievedDoc


pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


@dataclass
class CountingRetriever:
    """Retriever stub tracking how many times ``search`` is invoked."""

    calls: int = 0

    def search(self, query: str, k: int = 5):  # type: ignore[override]
        self.calls += 1
        return [
            RetrievedDoc(
                id=f"{query}:{idx}",
                text=f"{query} fact {idx}.",
                score=float(k - idx),
            )
            for idx in range(k)
        ]


def test_pipeline_uses_cache_for_repeated_queries() -> None:
    retriever = CountingRetriever()
    pipeline = FactPipeline(retriever=retriever, cache_ttl=1_000.0, cache_size=8, top_k=2)

    first = pipeline.run("alpha")
    second = pipeline.run("alpha")

    assert first == second
    assert retriever.calls == 1


def test_top_k_change_invalidates_cached_results() -> None:
    retriever = CountingRetriever()
    pipeline = FactPipeline(retriever=retriever, cache_ttl=1_000.0, cache_size=8, top_k=3)

    pipeline.run("beta")
    assert retriever.calls == 1

    pipeline.top_k = 1
    pipeline.run("beta")

    assert retriever.calls == 2


def test_updating_retriever_clears_cached_results() -> None:
    retriever_one = CountingRetriever()
    pipeline = FactPipeline(
        retriever=retriever_one, cache_ttl=1_000.0, cache_size=8, top_k=2
    )

    pipeline.run("gamma")
    assert retriever_one.calls == 1

    retriever_two = CountingRetriever()
    pipeline.update_retriever(retriever_two)
    pipeline.run("gamma")

    assert retriever_one.calls == 1
    assert retriever_two.calls == 1

