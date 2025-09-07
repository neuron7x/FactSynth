from __future__ import annotations
import math
import re
from collections import Counter
from typing import Dict, Any

def _text_stats(text: str) -> Dict[str, float]:
    n = len(text)
    if n == 0:
        return {"len": 0, "uniq_ratio": 0.0, "alpha_ratio": 0.0, "digit_ratio": 0.0, "whitespace_ratio": 0.0, "entropy": 0.0}
    uniq_ratio = len(set(text)) / n
    alpha = sum(ch.isalpha() for ch in text) / n
    digit = sum(ch.isdigit() for ch in text) / n
    space = sum(ch.isspace() for ch in text) / n
    cnt = Counter(text)
    probs = [c / n for c in cnt.values()]
    entropy = -sum(p * math.log(p + 1e-12, 2) for p in probs)
    return {"len": n, "uniq_ratio": uniq_ratio, "alpha_ratio": alpha, "digit_ratio": digit, "whitespace_ratio": space, "entropy": entropy}

def reflect_intent(intent: str, length: int) -> str:
    # Trim, normalize spaces, cut to length
    intent = re.sub(r"\s+", " ", intent).strip()
    return intent[: max(0, length)]

def score_payload(payload: Dict[str, Any]) -> float:
    """Deterministic composite score in [0,1] based on simple text stats.

    Inputs:
      - payload["text"]: str (optional)
      - payload["targets"]: list[str] (optional) — keywords to match

    Heuristics (weights sum to 1):
      - Coverage by keywords (0.4)
      - Normalized length saturation (0.3) up to 500 chars
      - Alphabetic density (0.2)
      - Entropy normalization (0.1)
    """
    text = str(payload.get("text", ""))
    targets = payload.get("targets") or []
    stats = _text_stats(text)
    # 1) keyword coverage
    cov = 0.0
    if targets:
        found = sum(1 for t in targets if t and t.lower() in text.lower())
        cov = found / len([t for t in targets if t])
    # 2) length saturation up to 500
    length_sat = min(1.0, stats["len"] / 500.0)
    # 3) alpha density as a signal
    alpha = stats["alpha_ratio"]
    # 4) entropy normalization (0..log2(256)≈8)
    ent = min(1.0, stats["entropy"] / 8.0)
    score = 0.4 * cov + 0.3 * length_sat + 0.2 * alpha + 0.1 * ent
    return round(float(score), 4)

def glrtpm_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Toy GLRTPM pipeline preserving API shape but adding structured output."""
    text = str(payload.get("text", ""))
    stages = []
    # ingest
    stages.append({"stage": "ingest", "ok": True, "n_bytes": len(text.encode("utf-8"))})
    # normalize
    norm = re.sub(r"\s+", " ", text).strip()
    stages.append({"stage": "normalize", "ok": True, "len": len(norm)})
    # analyze (keywords)
    tokens = [t for t in re.split(r"\W+", norm.lower()) if t]
    freq = Counter(tokens).most_common(5)
    stages.append({"stage": "analyze", "ok": True, "top_tokens": freq})
    # synthesize (echo first 120 chars)
    synth = norm[:120]
    stages.append({"stage": "synthesize", "ok": True, "preview": synth})
    # score
    s = score_payload({"text": norm, "targets": [t for t, _ in freq]})
    stages.append({"stage": "score", "ok": True, "score": s})
    # finalize
    result = {"summary": synth, "score": s, "tokens": len(tokens)}
    stages.append({"stage": "finalize", "ok": True})
    return {"ok": True, "stages": stages, "result": result}
