import pytest
from pydantic import ValidationError

from factsynth_ultimate.core.factsynth_lock import FactSynthLock

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def minimal_lock_data() -> dict:
    return {
        "verdict": {"decision": "supported"},
        "evidence": [
            {"source_id": "1", "source": "url", "content": "text"}
        ],
    }


def test_unknown_field_in_nested_model_rejected():
    data = minimal_lock_data()
    data["evidence"][0]["unexpected"] = "value"

    with pytest.raises(ValidationError):
        FactSynthLock.model_validate(data)
