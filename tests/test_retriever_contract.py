import asyncio

import pytest

from factsynth_ultimate.services.evaluator import evaluate_claim
from factsynth_ultimate.services.retrievers.base import RetrievedDoc

def test_evaluate_claim_closes_sync_retriever():
    class DummyRetriever:
        def __init__(self):
            self.closed = False

        def search(self, _query):
            return [RetrievedDoc(id="1", text="t", score=1.0)]

        def close(self):
            self.closed = True

    retriever = DummyRetriever()

    evaluate_claim("alpha", retriever=retriever)

    assert retriever.closed

@pytest.mark.asyncio
async def test_evaluate_claim_closes_async_retriever():
    class DummyRetriever:
        def __init__(self):
            self.closed = False

        def search(self, _query):
            return []

        async def aclose(self):
            self.closed = True

    retriever = DummyRetriever()

    evaluate_claim("beta", retriever=retriever)
    await asyncio.sleep(0)

    assert retriever.closed

def test_evaluate_claim_rejects_missing_search():
    class BadRetriever:
        def close(self):  # pragma: no cover - no-op
            pass

    with pytest.raises(TypeError):
        evaluate_claim("gamma", retriever=BadRetriever())

def test_evaluate_claim_rejects_noncallable_search():
    class BadRetriever:
        search = None

    with pytest.raises(TypeError):
        evaluate_claim("delta", retriever=BadRetriever())
