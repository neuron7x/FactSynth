from hypothesis import given
from hypothesis import strategies as st

from factsynth_ultimate.domain.models import Claim, ClaimStatus


@given(st.text(min_size=1, max_size=200))
def test_claim_defaults(text: str) -> None:
    c = Claim(text=text)
    assert c.status == ClaimStatus.pending  # noqa: S101
