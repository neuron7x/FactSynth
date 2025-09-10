import inspect
import threading

from fastapi.params import Depends as DependsParam

from app.api import verify as verify_mod
from app.services.evaluator import evaluate_claim


def test_evaluate_claim_composes_and_closes():
    class DummyRetriever:
        def __init__(self):
            self.closed = False

        def search(self, q):
            return [(q, 1.0)]

        def close(self):
            self.closed = True

    retriever = DummyRetriever()

    result = evaluate_claim(
        "alpha",
        policy_check=lambda _: {"allowed": True},
        scoring=lambda _: 0.5,
        diversity=lambda _: 0.1,
        nli=lambda _: {"label": "neutral"},
        retriever=retriever,
    )

    assert result["policy"] == {"allowed": True}
    assert result["score"] == 0.5  # noqa: PLR2004
    assert result["diversity"] == 0.1  # noqa: PLR2004
    assert result["nli"] == {"label": "neutral"}
    assert result["evidence"] == [("alpha", 1.0)]
    assert retriever.closed


def test_verify_uses_retriever_dependency_and_exposes_lock():
    assert isinstance(verify_mod.fs_lock, type(threading.Lock()))
    assert inspect.isgeneratorfunction(verify_mod.build_retriever)

    sig = inspect.signature(verify_mod.verify)
    params = list(sig.parameters.values())
    assert any(
        isinstance(p.default, DependsParam) and p.default.dependency is verify_mod.build_retriever
        for p in params
    )

    class DummyRetriever:
        def __init__(self):
            self.closed = False

        def search(self, q):
            return [(q, 1.0)]

        def close(self):
            self.closed = True

    req = verify_mod.VerifyRequest(
        claim="alpha", locale="en", max_sources=5, allow_untrusted=False
    )
    retriever = DummyRetriever()
    result = verify_mod.verify(req, retriever=retriever)
    assert isinstance(result, verify_mod.FactSynthLock)
    assert retriever.closed
