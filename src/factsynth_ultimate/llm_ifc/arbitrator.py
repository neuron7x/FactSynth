"""Simple arbitrator for model candidate responses."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Candidate:
    """Response candidate from an LLM."""

    model: str
    quality: float  # [0,1]
    context: float  # [0,1]
    text: str


def choose(
    cands: List[Candidate], w1: float = 0.5, w2: float = 0.5
) -> Dict[str, Optional[str] | float]:
    """Return the best candidate based on weighted quality and context."""

    if not cands:
        return {"winner": None, "score": 0.0, "text": ""}
    scored = [(c, w1 * float(c.quality) + w2 * float(c.context)) for c in cands]
    best = max(scored, key=lambda x: x[1])
    return {"winner": best[0].model, "score": float(best[1]), "text": best[0].text}
