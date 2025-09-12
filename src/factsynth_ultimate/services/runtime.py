from __future__ import annotations

import math
import re
import time
from collections import Counter
from collections.abc import Iterable
from typing import Any

from ..core.metrics import SCORING_TIME
from ..schemas.requests import ScoreReq

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _text_stats(text: str) -> dict[str, float]:
    """Compute character-based metrics for *text*.

    Returns a dictionary with:

    - ``len``: total number of characters.
    - ``uniq_ratio``: proportion of unique characters.
    - ``alpha_ratio``: fraction of alphabetic characters.
    - ``digit_ratio``: fraction of digit characters.
    - ``whitespace_ratio``: fraction of whitespace characters.
    - ``entropy``: Shannon entropy of character distribution in bits.
    """
    n = len(text)
    if n == 0:
        return {
            "len": 0,
            "uniq_ratio": 0.0,
            "alpha_ratio": 0.0,
            "digit_ratio": 0.0,
            "whitespace_ratio": 0.0,
            "entropy": 0.0,
        }
    uniq_ratio = len(set(text)) / n
    alpha = sum(ch.isalpha() for ch in text) / n
    digit = sum(ch.isdigit() for ch in text) / n
    space = sum(ch.isspace() for ch in text) / n
    cnt = Counter(text)
    probs = [c / n for c in cnt.values()]
    entropy = -sum(p * math.log(p, 2) for p in probs if p > 0)
    return {
        "len": n,
        "uniq_ratio": uniq_ratio,
        "alpha_ratio": alpha,
        "digit_ratio": digit,
        "whitespace_ratio": space,
        "entropy": entropy,
    }


def reflect_intent(intent: str, length: int) -> str:
    intent = re.sub(r"\s+", " ", intent).strip()
    return intent[: max(0, length)]


def _coverage(text: str, targets: Iterable[str]) -> float:
    if not targets:
        return 0.0
    words = set(_WORD_RE.findall(text.lower()))
    toks = [t.lower() for t in targets if t]
    if not toks:
        return 0.0
    found = sum(1 for t in toks if t in words)
    return found / len(toks)


def _score_impl(req: ScoreReq) -> float:
    s = _text_stats(req.text)
    cov = _coverage(req.text, req.targets or [])
    length_sat = min(1.0, s["len"] / 500.0)
    alpha = s["alpha_ratio"]
    ent = min(1.0, s["entropy"] / 8.0)
    score = 0.4 * cov + 0.3 * length_sat + 0.2 * alpha + 0.1 * ent
    return round(float(score), 4)


def score_payload(payload: dict[str, Any]) -> float:
    req = ScoreReq(**(payload or {}))
    t0 = time.perf_counter()
    val = _score_impl(req)
    SCORING_TIME.observe(max(0.0, time.perf_counter() - t0))
    return val


def tokenize_preview(text: str, max_tokens: int = 256) -> list[str]:
    toks = _WORD_RE.findall(text)
    return toks[:max_tokens]
