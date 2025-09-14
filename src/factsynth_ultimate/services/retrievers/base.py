from __future__ import annotations

"""Protocol definitions for document retrievers."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class RetrievedDoc:
    """Result returned by a retriever search."""

    id: str
    text: str
    score: float


@runtime_checkable
class Retriever(Protocol):
    """Protocol for search backends used by :func:`evaluate_claim`."""

    def search(self, query: str, k: int = 5) -> Iterable[RetrievedDoc]:
        """Return up to ``k`` documents relevant to ``query``."""

    def close(self) -> None:  # pragma: no cover - optional
        """Release any open resources."""

    async def aclose(self) -> None:  # pragma: no cover - optional
        """Asynchronously release any open resources."""
