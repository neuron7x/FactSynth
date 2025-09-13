import pytest
from pydantic import ValidationError

from factsynth_ultimate.core.factsynth_lock import Decision, FactSynthLock, Verdict

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_unknown_field_rejected():
    data = {
        "verdict": {"decision": "supported"},
        "evidence": [{"source": "https://example.com", "content": "text"}],
        "unexpected": "value",
    }

    with pytest.raises(ValidationError):
        FactSynthLock.model_validate(data)


def test_invalid_decision_rejected():
    with pytest.raises(ValidationError):
        Verdict.model_validate({"decision": "maybe"})


def test_verdict_rejects_unknown_field():
    with pytest.raises(ValidationError):
        Verdict.model_validate({"decision": Decision.SUPPORTED, "extra": "value"})


def test_lock_requires_evidence():
    data = {"verdict": {"decision": "supported"}, "evidence": []}

    with pytest.raises(ValidationError):
        FactSynthLock.model_validate(data)
