import math

import pytest
from pydantic import ValidationError

from factsynth_ultimate.services import runtime

def test_text_stats_empty():
    assert runtime._text_stats("") == {
        "len": 0,
        "uniq_ratio": 0.0,
        "alpha_ratio": 0.0,
        "digit_ratio": 0.0,
        "whitespace_ratio": 0.0,
        "entropy": 0.0,
    }

def test_text_stats_mixed():
    text = "abc123"
    s = runtime._text_stats(text)
    n = len(text)
    entropy = -sum((1 / n) * math.log2(1 / n) for _ in range(n))
    assert s["len"] == n
    assert s["uniq_ratio"] == 1.0
    assert s["alpha_ratio"] == pytest.approx(0.5)
    assert s["digit_ratio"] == pytest.approx(0.5)
    assert s["whitespace_ratio"] == 0.0
    assert s["entropy"] == pytest.approx(entropy)

def test_text_stats_non_ascii():
    text = "你好123"
    s = runtime._text_stats(text)
    n = len(text)
    assert s["len"] == n
    assert s["alpha_ratio"] == pytest.approx(2 / n)
    assert s["digit_ratio"] == pytest.approx(3 / n)

def test_reflect_intent_trimming_and_collapse():
    assert runtime.reflect_intent("  Hello   world \n", 7) == "Hello w"

def test_coverage_scenarios():
    text = "alpha beta gamma"
    assert runtime._coverage(text, []) == 0.0
    assert runtime._coverage(text, ["alpha", "delta", "gamma"]) == pytest.approx(2 / 3)
    assert runtime._coverage(text, ["alpha", "beta", "gamma"]) == 1.0

def test_score_payload_varied():
    payload = {"text": "alpha beta 123", "targets": ["alpha", "gamma"]}
    s = runtime._text_stats(payload["text"])
    cov = runtime._coverage(payload["text"], payload["targets"])
    length_sat = min(1.0, s["len"] / 500.0)
    alpha = s["alpha_ratio"]
    ent = min(1.0, s["entropy"] / 8.0)
    expected = round(0.4 * cov + 0.3 * length_sat + 0.2 * alpha + 0.1 * ent, 4)
    assert runtime.score_payload(payload) == expected

def test_tokenize_preview_truncation_and_non_ascii():
    text = "你好 世界 alpha beta"  # four tokens
    max_tokens = 3
    toks = runtime.tokenize_preview(text, max_tokens=max_tokens)
    assert toks == ["你好", "世界", "alpha"]
    assert len(toks) == max_tokens

def test_score_payload_malformed_payload():
    with pytest.raises(ValidationError):
        runtime.score_payload({"text": 123})
