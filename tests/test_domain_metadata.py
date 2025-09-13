import pytest
from pydantic import ValidationError

from factsynth_ultimate.schemas.requests import DomainMetadata, ScoreReq

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_domain_metadata_valid():
    meta = DomainMetadata(region="eu", language="en", time_range="2020-2021")
    req = ScoreReq(text="t", domain=meta)
    assert req.domain == meta


def test_domain_metadata_invalid_region():
    with pytest.raises(ValidationError):
        ScoreReq(text="t", domain={"region": "", "language": "en", "time_range": "2020"})


@pytest.mark.parametrize("kwargs", [
    {},
    {"targets": []},
])
def test_score_req_requires_text_or_targets(kwargs):
    with pytest.raises(ValidationError):
        ScoreReq(**kwargs)


def test_score_req_accepts_text_or_targets():
    assert ScoreReq(text="x").text == "x"
    assert ScoreReq(targets=["a"]).targets == ["a"]
