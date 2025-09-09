from __future__ import annotations

from .base import ScoreBackend
from ..schemas.requests import ScoreReq


class SemanticBackend(ScoreBackend):
    """Placeholder backend for semantic coverage scoring."""

    def score(self, req: ScoreReq) -> float:  # pragma: no cover - example stub
        raise NotImplementedError("Semantic backend not implemented")
