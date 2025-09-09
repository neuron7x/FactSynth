from __future__ import annotations

import re
import time
from typing import Any, Dict

from ..backends import get_backend
from ..core.metrics import SCORING_TIME
from ..schemas.requests import ScoreReq

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def reflect_intent(intent: str, length: int) -> str:
    intent = re.sub(r"\s+", " ", intent).strip()
    return intent[: max(0, length)]


def score_payload(payload: Dict[str, Any], backend: str | None = None) -> float:
    req = ScoreReq(**(payload or {}))
    t0 = time.perf_counter()
    val = get_backend(backend).score(req)
    SCORING_TIME.observe(max(0.0, time.perf_counter() - t0))
    return val


def tokenize_preview(text: str, max_tokens: int = 256) -> list[str]:
    toks = _WORD_RE.findall(text)
    return toks[:max_tokens]
