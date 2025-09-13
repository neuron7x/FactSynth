import pytest
from pydantic import ValidationError

from factsynth_ultimate.services.runtime import (
    _text_stats,
    reflect_intent,
    _coverage,
    score_payload,
    tokenize_preview,
)

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_text_stats_empty():
    stats = _text_stats("")
    assert stats == {
        "len": 0,
        "uniq_ratio": 0.0,
        "alpha_ratio": 0.0,
        "digit_ratio": 0.0,
        "whitespace_ratio": 0.0,
        "entropy": 0.0,
    }


def test_text_stats_mixed_and_non_ascii():
    text = "Abc123 \u03b1\u03b2"  # includes Greek letters
    stats = _text_stats(text)
    assert stats["len"] == len(text)
    # Ratios fall within [0, 1]
    for key in ["uniq_ratio", "alpha_ratio", "digit_ratio", "whitespace_ratio"]:
        assert 0.0 <= stats[key] <= 1.0
    assert stats["entropy"] > 0


def test_reflect_intent_truncates_and_collapses_whitespace():
    intent = "  Hello    world\nagain  "
    assert reflect_intent(intent, 11) == "Hello world"


def test_reflect_intent_handles_non_ascii():
    intent = "  \u041f\u0440\u0438\u0432\u0435\u0442    \u043c\u0438\u0440  "  # "Привет мир"
    assert reflect_intent(intent, 20) == "\u041f\u0440\u0438\u0432\u0435\u0442 \u043c\u0438\u0440"


def test_coverage_cases():
    text = "cat dog mouse"
    assert _coverage(text, []) == 0.0
    assert _coverage(text, ["cat", "bird"]) == pytest.approx(0.5)
    assert _coverage(text, ["cat", "dog"]) == 1.0


def test_score_payload_expected_values():
    assert score_payload({}) == 0.0
    payload = {"text": "alpha beta", "targets": ["alpha", "gamma"]}
    assert score_payload(payload) == pytest.approx(0.4216, rel=1e-4)


def test_score_payload_malformed_payload_raises():
    with pytest.raises(ValidationError):
        score_payload({"text": 123, "targets": [456]})


def test_tokenize_preview_truncates():
    text = " ".join(f"w{i}" for i in range(300))
    tokens = tokenize_preview(text, max_tokens=50)
    assert len(tokens) == 50
    assert tokens[0] == "w0" and tokens[-1] == "w49"
