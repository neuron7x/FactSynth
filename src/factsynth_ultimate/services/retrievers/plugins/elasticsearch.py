"""Example ElasticSearch retriever plugin used for documentation and tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..base import RetrievedDoc, Retriever


@dataclass
class ElasticSearchRetriever:
    """Very small retriever that simulates ElasticSearch queries."""

    host: str = "http://localhost:9200"
    index: str = "facts"
    timeout: float = 1.0

    def search(self, query: str, k: int = 5) -> list[RetrievedDoc]:
        """Return a deterministic document describing the simulated query."""

        snippet = (
            f"ElasticSearch[{self.index}]@{self.host} simulated query: {query}"
        )
        doc = RetrievedDoc(id=f"{self.index}:0", text=snippet, score=1.0)
        return [doc][: max(1, k)]

    def close(self) -> None:  # pragma: no cover - optional protocol hook
        """Close the retriever (no-op for the simulated backend)."""

        return None

    async def aclose(self) -> None:  # pragma: no cover - optional protocol hook
        """Async close hook provided for completeness."""

        return None


def create_elasticsearch_retriever(**options: Any) -> Retriever:
    """Factory function registered as the ElasticSearch entry point."""

    return ElasticSearchRetriever(**options)


__all__ = [
    "ElasticSearchRetriever",
    "create_elasticsearch_retriever",
]
