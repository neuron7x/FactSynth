"""Local in-memory retriever used primarily for tests."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar

from ...tokenization import tokenize
from .base import RetrievedDoc, Retriever


@dataclass
class Fixture:
    """Simple container for fixture text."""

    id: str
    text: str


class LocalFixtureRetriever:
    """In-memory search over a list of fixtures.

    The search implementation tokenizes both the query and fixture text and
    scores candidates by Jaccard overlap of token sets. To improve matching for
    Ukrainian queries against English fixtures we first substitute common
    Ukrainian keywords with their English equivalents before tokenization.
    """

    _UA_TO_EN: ClassVar[dict[str, str]] = {
        "мікросервіси": "microservices",
        "мікросервіс": "microservice",
        "хмара": "cloud",
    }

    def __init__(self, fixtures: Iterable[Fixture], locale: str = "en"):
        self.fixtures = list(fixtures)
        self.locale = locale.lower()

    def _translate_query(self, query: str) -> str:
        """Translate common Ukrainian keywords to English."""

        if self.locale != "en":
            return query

        q = query.lower()
        for ua, en in self._UA_TO_EN.items():
            q = re.sub(rf"\b{ua}\b", en, q)
        return q

    def close(self) -> None:
        """Close hook to satisfy the :class:`Retriever` protocol."""

        return None

    async def aclose(self) -> None:
        """Async close hook to satisfy the :class:`Retriever` protocol."""

        return None

    def search(self, query: str, k: int = 5) -> list[RetrievedDoc]:
        """Return top ``k`` fixtures ranked by similarity to ``query``."""

        translated = self._translate_query(query)
        q_tokens = {t.lower() for t in tokenize(translated)}
        results: list[RetrievedDoc] = []
        for fix in self.fixtures:
            f_tokens = {t.lower() for t in tokenize(fix.text)}
            if q_tokens or f_tokens:
                score = len(q_tokens & f_tokens) / len(q_tokens | f_tokens)
            else:
                score = 0.0
            results.append(RetrievedDoc(id=fix.id, text=fix.text, score=score))
        results.sort(key=lambda d: d.score, reverse=True)
        return results[:k]


_DEFAULT_FIXTURES: dict[str, tuple[Fixture, ...]] = {
    "en": (
        Fixture(id="default", text="alpha is the first letter"),
        Fixture(id="kyiv", text="Kyiv is the capital of Ukraine."),
    ),
    "uk": (
        Fixture(id="default_uk", text="Київ — столиця України."),
        Fixture(id="dnipro", text="Річка Дніпро протікає через Київ."),
    ),
}


def _fixtures_for_locale(locale: str) -> Iterable[Fixture]:
    normalized = locale.lower()
    fixtures = _DEFAULT_FIXTURES.get(normalized)
    if fixtures is not None:
        return fixtures
    return _DEFAULT_FIXTURES["en"]


def create_fixture_retriever(locale: str = "en") -> Retriever:
    """Return a default retriever instance for entry-point loading."""

    normalized = locale.lower()
    fixtures = _fixtures_for_locale(normalized)
    return LocalFixtureRetriever(fixtures, locale=normalized)
