from __future__ import annotations

from factsynth.services.bias_filter import analyze_text


def test_bias_heuristics() -> None:
    res = analyze_text("Це очевидно єдина причина успіху.")
    kinds = {f.kind for f in res}
    assert "overconfidence" in kinds
    assert "single_cause" in kinds
