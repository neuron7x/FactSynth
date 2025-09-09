from __future__ import annotations

from abc import ABC, abstractmethod

from ..schemas.requests import ScoreReq


class ScoreBackend(ABC):
    """Abstract interface for pluggable scoring backends."""

    @abstractmethod
    def score(self, req: ScoreReq) -> float:
        """Return a score in ``[0, 1]`` for ``req``."""
        raise NotImplementedError
