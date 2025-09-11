import inspect

from fastapi.params import Depends as DependsParam
from pydantic import BaseModel

from factsynth_ultimate.api import verify as verify_mod
from factsynth_ultimate.services.evaluator import evaluate_claim

EXPECTED_SCORE = 0.5
EXPECTED_DIVERSITY = 0.1
EVIDENCE_SCORE = 1.0


def test_evaluate_claim_composes_and_closes():
    class DummyRetriever:
        def __init__(self):
            self.closed = False

        def search(self, q):
            return [(q, EVIDENCE_SCORE)]

        def close(self):
            self.closed = True

    retriever = DummyRetriever()

    result = evaluate_claim(
        "alpha",
        policy_check=lambda _: {"allowed": True},
        scoring=lambda _: EXPECTED_SCORE,
        diversity=lambda _: EXPECTED_DIVERSITY,
        nli=lambda _: {"label": "neutral"},
        retriever=retriever,
    )

    assert result["policy"] == {"allowed": True}
    assert result["score"] == EXPECTED_SCORE
    assert result["diversity"] == EXPECTED_DIVERSITY
    assert result["nli"] == {"label": "neutral"}
    assert result["evidence"] == [("alpha", EVIDENCE_SCORE)]
    assert retriever.closed


def test_verify_depends_on_evaluate_and_exposes_model():
    assert issubclass(verify_mod.FactSynthLock, BaseModel)

    sig = inspect.signature(verify_mod.verify)
    params = list(sig.parameters.values())
    assert any(
        isinstance(p.default, DependsParam) and p.default.dependency is evaluate_claim
        for p in params
    )
