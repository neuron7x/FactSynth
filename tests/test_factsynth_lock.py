import pytest
from pydantic import ValidationError

from factsynth_ultimate.core.factsynth_lock import Decision, FactSynthLock, Verdict

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_unknown_field_rejected():
    data = {
        "verdict": {"decision": "confirmed"},
        "evidence": [{"source_id": "1", "source": "url", "content": "text"}],
        "unexpected": "value",
    }

    with pytest.raises(ValidationError):
        FactSynthLock.model_validate(data)


def test_invalid_decision_rejected():
    with pytest.raises(ValidationError):
        Verdict.model_validate({"decision": "maybe"})


def test_verdict_rejects_unknown_field():
    with pytest.raises(ValidationError):
        Verdict.model_validate({"decision": Decision.CONFIRMED, "extra": "value"})


def test_lock_requires_evidence():
    data = {"verdict": {"decision": "confirmed"}, "evidence": []}

    with pytest.raises(ValidationError):
        FactSynthLock.model_validate(data)


@pytest.mark.parametrize(
    "legacy,expected",
    [
        ("supported", Decision.CONFIRMED),
        ("partially_supported", Decision.MIXED),
        ("not_provable", Decision.NOT_ENOUGH_EVIDENCE),
    ],
)
def test_legacy_decisions_normalized(legacy: str, expected: Decision):
    data = {
        "verdict": {"decision": legacy},
        "evidence": [{"source_id": "1", "source": "url", "content": "text"}],
    }

    lock = FactSynthLock.model_validate(data)
    assert lock.verdict.decision is expected
