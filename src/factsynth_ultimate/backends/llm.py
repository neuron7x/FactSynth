from __future__ import annotations

from .base import ScoreBackend
from ..schemas.requests import ScoreReq


class LLMBackend(ScoreBackend):
    """Placeholder backend that could score using an LLM."""

    def score(self, req: ScoreReq) -> float:  # pragma: no cover - example stub
        raise NotImplementedError("LLM backend not implemented")
