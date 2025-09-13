import pytest
from pydantic import ValidationError

from factsynth_ultimate.core.factsynth_lock import (
    FactSynthLock,
    Recommendations,
    SourceSynthesis,
    Traceability,
    Verdict,
)


def test_verdict_enforces_enum_and_no_extra(httpx_mock):
    httpx_mock.reset(assert_all_responses_were_requested=False)
    with pytest.raises(ValidationError):
        Verdict(decision="maybe")
    with pytest.raises(ValidationError):
        Verdict(decision="supported", unknown="field")


def test_lock_rejects_unknown_fields(httpx_mock):
    httpx_mock.reset(assert_all_responses_were_requested=False)
    v = Verdict(decision="supported")
    ss = SourceSynthesis(summary="s")
    tr = Traceability()
    rec = Recommendations()
    with pytest.raises(ValidationError):
        FactSynthLock(
            verdict=v,
            source_synthesis=ss,
            traceability=tr,
            recommendations=rec,
            unknown="field",
        )
