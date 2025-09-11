import inspect

from fastapi.params import Depends as DependsParam
from pydantic import BaseModel

from factsynth_ultimate.api import verify as verify_mod
from factsynth_ultimate.services.evaluator import evaluate_claim


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


def test_verify_depends_on_evaluate_and_exposes_model():
    assert issubclass(verify_mod.FactSynthLock, BaseModel)

    sig = inspect.signature(verify_mod.verify)
    params = list(sig.parameters.values())
    assert any(
        isinstance(p.default, DependsParam) and p.default.dependency is evaluate_claim
        for p in params
    )
