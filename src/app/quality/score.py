from __future__ import annotations

from typing import Sequence


def compute_sqs(text: str) -> float:
    """Compute a simple Semantic Quality Score (SQS).

    The score is the ratio of unique words to total words.
    """
    tokens = text.split()
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def compute_ess(texts: Sequence[str]) -> float:
    """Compute a rudimentary Ensemble Semantic Score (ESS).

    The score is the average SQS across a collection of texts.
    """
    if not texts:
        return 0.0
    scores = [compute_sqs(t) for t in texts]
    return sum(scores) / len(scores)


__all__ = ["compute_ess", "compute_sqs"]
