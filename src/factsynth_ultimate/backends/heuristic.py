from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, Iterable

from .base import ScoreBackend
from ..schemas.requests import ScoreReq

_WORD_RE = re.compile(r"\w+", re.UNICODE)


class HeuristicBackend(ScoreBackend):
    """Default heuristic scoring backend."""

    def _text_stats(self, text: str) -> Dict[str, float]:
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

    def _coverage(self, text: str, targets: Iterable[str]) -> float:
        if not targets:
            return 0.0
        words = set(_WORD_RE.findall(text.lower()))
        toks = [t.lower() for t in targets if t]
        if not toks:
            return 0.0
        found = sum(1 for t in toks if t in words)
        return found / len(toks)

    def score(self, req: ScoreReq) -> float:
        stats = self._text_stats(req.text)
        cov = self._coverage(req.text, req.targets or [])
        length_sat = min(1.0, stats["len"] / 500.0)
        alpha = stats["alpha_ratio"]
        ent = min(1.0, stats["entropy"] / 8.0)
        score = 0.4 * cov + 0.3 * length_sat + 0.2 * alpha + 0.1 * ent
        return round(float(score), 4)
