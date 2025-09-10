from __future__ import annotations

from itertools import combinations
from typing import Sequence

MIN_TEXTS = 2


def lexical_diversity(text: str) -> float:
    """Calculate lexical diversity of a text as unique tokens over total tokens."""
    tokens = text.split()
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def pairwise_jaccard(texts: Sequence[str]) -> float:
    """Average pairwise Jaccard similarity across texts."""
    if len(texts) < MIN_TEXTS:
        return 1.0
    pairs = list(combinations(texts, MIN_TEXTS))
    scores = []
    for a, b in pairs:
        set_a, set_b = set(a.split()), set(b.split())
        union = set_a | set_b
        if not union:
            scores.append(0.0)
        else:
            scores.append(len(set_a & set_b) / len(union))
    return sum(scores) / len(scores)


__all__ = ["lexical_diversity", "pairwise_jaccard"]
