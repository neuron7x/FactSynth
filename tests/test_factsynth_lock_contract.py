import pytest
from pydantic import ValidationError

from factsynth_ultimate.core.factsynth_lock import (
    FactSynthLock,
    Recommendations,
    SourceSynthesis,
    Traceability,
    Verdict,
)

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_verdict_enforces_enum_and_no_extra():
    with pytest.raises(ValidationError):
        Verdict(decision="maybe")
    with pytest.raises(ValidationError):
        Verdict(decision="supported", unknown="field")


def test_lock_rejects_unknown_fields():
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
