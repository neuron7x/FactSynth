"""Composable pipeline executing the fact synthesis flow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from factsynth_ultimate.formatting import ensure_period, sanitize
from factsynth_ultimate.services.retrievers.base import RetrievedDoc, Retriever
from factsynth_ultimate.services.retrievers.local import create_fixture_retriever


class FactPipelineError(RuntimeError):
    """Base class for errors raised during fact synthesis."""


class EmptyQueryError(FactPipelineError):
    """Raised when the incoming query is blank."""


class SearchError(FactPipelineError):
    """Raised when the retriever fails to execute."""


class NoFactsFoundError(SearchError):
    """Raised when the retriever returns no usable documents."""


class AggregationError(FactPipelineError):
    """Raised when the aggregation or formatting step fails."""


Ranker = Callable[[Iterable[RetrievedDoc], int], Sequence[RetrievedDoc]]
Aggregator = Callable[[Sequence[RetrievedDoc]], str]
Formatter = Callable[[str], str]


def default_ranker(results: Iterable[RetrievedDoc], limit: int) -> list[RetrievedDoc]:
    """Return the top ``limit`` results sorted by score."""

    ranked = sorted(results, key=lambda doc: doc.score, reverse=True)
    seen: set[str] = set()
    unique: list[RetrievedDoc] = []
    for doc in ranked:
        if doc.id in seen:
            continue
        unique.append(doc)
        seen.add(doc.id)
        if len(unique) >= max(1, limit):
            break
    return unique


def default_aggregator(docs: Sequence[RetrievedDoc]) -> str:
    """Combine supporting documents into a single paragraph."""

    fragments: list[str] = []
    for doc in docs:
        text = doc.text.strip()
        if not text:
            continue
        if text[-1] not in ".!?…":
            text = f"{text}."
        fragments.append(text)
    if not fragments:
        raise AggregationError("No supporting text to aggregate")
    return " ".join(fragments)


def default_formatter(text: str) -> str:
    """Normalize aggregated text and ensure it ends with a period."""

    cleaned = sanitize(
        text,
        forbid_questions=False,
        forbid_headings=True,
        forbid_lists=True,
        forbid_emojis=True,
    ).strip()
    if not cleaned:
        raise AggregationError("Formatted text is empty")
    return ensure_period(cleaned)


@dataclass
class FactPipeline:
    """Execute retrieval, ranking, aggregation and formatting for ``query``."""

    retriever: Retriever | None = None
    top_k: int = 3
    ranker: Ranker = default_ranker
    aggregator: Aggregator = default_aggregator
    formatter: Formatter = default_formatter

    def __post_init__(self) -> None:
        if self.retriever is None:
            self.retriever = create_fixture_retriever()
        if self.top_k <= 0:
            raise ValueError("top_k must be positive")

    def run(self, query: str) -> str:
        """Execute the pipeline and return formatted supporting facts."""

        prepared = query.strip()
        if not prepared:
            raise EmptyQueryError("Query must not be empty")

        try:
            results = list(self.retriever.search(prepared, k=max(1, self.top_k)))
        except FactPipelineError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise SearchError("Search backend failed") from exc

        if not results:
            raise NoFactsFoundError(f"No facts found for '{prepared}'")

        ranked = list(self.ranker(results, self.top_k))
        if not ranked:
            raise NoFactsFoundError(f"No facts found for '{prepared}'")

        try:
            aggregated = self.aggregator(ranked)
        except FactPipelineError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise AggregationError("Failed to aggregate supporting facts") from exc

        if not aggregated.strip():
            raise AggregationError("Aggregation produced empty output")

        try:
            formatted = self.formatter(aggregated)
        except FactPipelineError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise AggregationError("Failed to format aggregated facts") from exc

        if not formatted.strip():
            raise AggregationError("Formatted output is empty")

        return formatted


__all__ = [
    "Aggregator",
    "FactPipeline",
    "FactPipelineError",
    "EmptyQueryError",
    "NoFactsFoundError",
    "AggregationError",
    "Ranker",
    "SearchError",
]
