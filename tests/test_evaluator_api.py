
from pydantic import BaseModel

from factsynth_ultimate.api import verify as verify_mod
from factsynth_ultimate.services.evaluator import evaluate_claim

SCORING_RESULT = 0.5
DIVERSITY_RESULT = 0.1


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
        scoring=lambda _: SCORING_RESULT,
        diversity=lambda _: DIVERSITY_RESULT,
        nli=lambda _: {"label": "neutral"},
        retriever=retriever,
    )

    assert result["policy"] == {"allowed": True}
    assert result["score"] == SCORING_RESULT
    assert result["diversity"] == DIVERSITY_RESULT
    assert result["nli"] == {"label": "neutral"}
    assert result["evidence"] == [("alpha", 1.0)]
    assert retriever.closed


def test_verify_exposes_models():
    assert issubclass(verify_mod.FactSynthLock, BaseModel)
    assert issubclass(verify_mod.VerifyRequest, BaseModel)
