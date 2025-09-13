import pytest
from pydantic import ValidationError

from factsynth_ultimate.core.factsynth_lock import FactSynthLock, Verdict

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_unknown_field_rejected(httpx_mock):
    httpx_mock.reset(assert_all_responses_were_requested=False)
    data = {
        "verdict": {"decision": "supported"},
        "source_synthesis": {"summary": "summary"},
        "traceability": {},
        "recommendations": {},
        "unexpected": "value",
    }

    with pytest.raises(ValidationError):
        FactSynthLock.model_validate(data)


def test_invalid_decision_rejected(httpx_mock):
    httpx_mock.reset(assert_all_responses_were_requested=False)
    with pytest.raises(ValidationError):
        Verdict.model_validate({"decision": "maybe"})
