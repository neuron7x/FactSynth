from __future__ import annotations

import os
import re
from dataclasses import dataclass

BIAS_ENABLED = os.getenv("BIAS_FILTER_ENABLED", "true").lower() == "true"


@dataclass
class BiasFinding:
    kind: str
    score: float
    span: str
    hint: str


_PATTERNS: dict[str, str] = {
    "overconfidence": r"\b(безсумнівно|очевидно|гарантовано|точно|на 100%)\b",
    "single_cause": r"\b(єдина|тільки одна|лише одна) причина\b",
    "survivorship": r"\b(усі успішні|успіх.*тільки)\b",  # noqa: RUF001
    "anchoring": r"\b(спочатку.*тому|раз так.*то)\b",
    "confirmation": r"\b(підтверджує мою думку|як і очікувалось)\b",  # noqa: RUF001
    "appeal_to_authority": r"\b(бо сказав експерт|нобелівський лауреат сказав)\b",  # noqa: RUF001
}


def analyze_text(text: str, max_findings: int = 10) -> list[BiasFinding]:
    findings: list[BiasFinding] = []
    for kind, pat in _PATTERNS.items():
        for match in re.finditer(pat, text, flags=re.I | re.U):
            findings.append(
                BiasFinding(kind, 0.4, match.group(0), "Переформулюй нейтрально/перевір джерела")
            )
            if len(findings) >= max_findings:
                return findings
    return findings


def filter_and_annotate(prompt: str, completion: str) -> dict:
    """Return a bias report for prompt and completion."""
    if not BIAS_ENABLED:
        return {"enabled": False, "findings": []}
    f1 = analyze_text(prompt or "")
    f2 = analyze_text(completion or "")
    return {
        "enabled": True,
        "findings": [
            *({"side": "prompt", **f.__dict__} for f in f1),
            *({"side": "completion", **f.__dict__} for f in f2),
        ],
    }
