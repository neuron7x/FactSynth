import pytest

from factsynth_ultimate import formatting

try:
    from hypothesis import given
    from hypothesis import strategies as st
except ModuleNotFoundError:  # pragma: no cover - optional
    pytest.skip("hypothesis not installed", allow_module_level=True)


@given(st.text(min_size=0, max_size=2000))
def test_sanitize_idempotent(s: str) -> None:
    once = formatting.sanitize(s)
    twice = formatting.sanitize(once)
    assert once == twice


@given(st.text(min_size=1, max_size=1000))
def test_ensure_period_postcondition(s: str) -> None:
    t = formatting.ensure_period(s)
    assert t.endswith(("!", "?", ".", "…"))

