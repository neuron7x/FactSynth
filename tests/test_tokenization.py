import pytest
import regex as re

try:
    from hypothesis import given
    from hypothesis import strategies as st
except ModuleNotFoundError:  # pragma: no cover - optional
    pytest.skip("hypothesis not installed", allow_module_level=True)

from factsynth_ultimate import tokenization

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)

whitespace = st.one_of(
    st.just(" "),
    st.just("\t"),
    st.just("\n"),
    st.just("\r"),
    st.just("\u00A0"),
)

non_ws_char = st.characters(categories=["L", "M", "N", "P", "S"])

alphabet = st.one_of(non_ws_char, whitespace)

deferred_text = st.text(alphabet, min_size=0, max_size=100)


@given(deferred_text)
def test_normalize_collapses_whitespace_and_strips_edges(s: str) -> None:
    norm = tokenization.normalize(s)
    assert "\u00A0" not in norm
    assert norm == norm.strip()
    assert not re.search(r"\s{2,}", norm)


@given(deferred_text)
def test_tokenize_deterministic(s: str) -> None:
    once = tokenization.tokenize(s)
    twice = tokenization.tokenize(s)
    norm_tokens = tokenization.tokenize(tokenization.normalize(s))
    assert once == twice == norm_tokens
