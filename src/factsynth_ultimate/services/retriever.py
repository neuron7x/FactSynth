"""Small in-memory text retriever used for testing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar, Iterable, List

from ..tokenization import tokenize


@dataclass
class Fixture:
    """Simple container for fixture text."""

    id: str
    text: str


@dataclass
class RetrievedDoc:
    """Result returned by a retriever search."""

    id: str
    text: str
    score: float


class LocalFixtureRetriever:
    """In-memory search over a list of fixtures.

    The search implementation tokenizes both the query and fixture text and
    scores candidates by Jaccard overlap of token sets. To improve matching for
    Ukrainian queries against English fixtures we first substitute common
    Ukrainian keywords with their English equivalents before tokenization.
    """

    # Common Ukrainian→English keyword replacements.
    _UA_TO_EN: ClassVar[dict[str, str]] = {
        "мікросервіси": "microservices",
        "мікросервіс": "microservice",
        "хмара": "cloud",
    }

    def __init__(self, fixtures: Iterable[Fixture]):
        self.fixtures = list(fixtures)

    def _translate_query(self, query: str) -> str:
        """Translate common Ukrainian keywords to English."""

        q = query.lower()
        for ua, en in self._UA_TO_EN.items():
            q = re.sub(rf"\b{ua}\b", en, q)
        return q

    def search(self, query: str, k: int = 5) -> List[RetrievedDoc]:
        """Return top ``k`` fixtures ranked by similarity to ``query``."""

        translated = self._translate_query(query)
        q_tokens = {t.lower() for t in tokenize(translated)}
        results: List[RetrievedDoc] = []
        for fix in self.fixtures:
            f_tokens = {t.lower() for t in tokenize(fix.text)}
            if q_tokens or f_tokens:
                score = len(q_tokens & f_tokens) / len(q_tokens | f_tokens)
            else:
                score = 0.0
            results.append(RetrievedDoc(id=fix.id, text=fix.text, score=score))
        results.sort(key=lambda d: d.score, reverse=True)
        return results[:k]
