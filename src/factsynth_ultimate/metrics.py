from __future__ import annotations
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ACTION_VERBS = [
    "запустити",
    "калібрувати",
    "визначити",
    "перевірити",
    "впровадити",
    "виміряти",
    "спростити",
    "скласти",
    "застосувати",
]


def relevance_cosine(intent: str, text: str) -> float:
    vec = TfidfVectorizer(min_df=1, ngram_range=(1, 2))
    X = vec.fit_transform([intent, text])
    return float(cosine_similarity(X[0], X[1])[0, 0])


def depth_score(text: str) -> float:
    cues = [
        "метрика",
        "обмеженн",
        "блокер",
        "горизонт",
        "асоціатив",
        "ризик",
        "дія за замовчуванням",
    ]
    hit = sum(c in text.lower() for c in cues)
    return min(1.0, hit / 7.0)


def applicability_score(text: str) -> float:
    hit = sum(v in text.lower() for v in ACTION_VERBS)
    return min(1.0, hit / 4.0)


def novelty_score(base: list[str] | None, text: str) -> float:
    if not base:
        return 0.5
    src = " ".join(base).lower().split()
    if not src:
        return 0.5
    out = set(text.lower().split())
    overlap = len([w for w in out if w in src]) / max(1, len(out))
    return max(0.0, min(1.0, 1.0 - overlap))


def format_ok(text: str, start_phrase: str) -> float:
    return 1.0 if (text.startswith(start_phrase) and "?" not in text) else 0.0


@dataclass
class JWeights:
    wF: float = 0.20
    wR: float = 0.30
    wD: float = 0.25
    wA: float = 0.15
    wN: float = 0.10


def j_index(
    intent: str,
    text: str,
    start_phrase: str,
    facts: list[str] | None = None,
    knowledge: list[str] | None = None,
) -> dict:
    F = format_ok(text, start_phrase)
    R = relevance_cosine(intent, text)
    D = depth_score(text)
    A = applicability_score(text)
    N = novelty_score((facts or []) + (knowledge or []), text)
    J = (
        JWeights().wF * F
        + JWeights().wR * R
        + JWeights().wD * D
        + JWeights().wA * A
        + JWeights().wN * N
    )
    return {"F": F, "R": R, "D": D, "A": A, "N": N, "J": J}
