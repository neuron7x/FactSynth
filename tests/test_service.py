from factsynth_ultimate.service import synthesize


def test_synthesize_limits_and_checksum():
    out = synthesize("one two three four five", max_tokens=2)
    assert out.startswith("one two |ck:")
    out2 = synthesize(" one   two \t  ", max_tokens=5)
    assert out2.startswith("one two |ck:")
    assert synthesize("abc", 10) == synthesize("abc", 10)
