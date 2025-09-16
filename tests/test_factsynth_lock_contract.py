import pytest
from pydantic import ValidationError

from factsynth_ultimate.core.factsynth_lock import FactSynthLock

def minimal_lock_data() -> dict:
    return {
        "verdict": {"decision": "confirmed"},
        "evidence": [{"source_id": "1", "source": "url", "content": "text"}],
    }

def test_unknown_field_in_nested_model_rejected():
    data = minimal_lock_data()
    data["evidence"][0]["unexpected"] = "value"

    with pytest.raises(ValidationError):
        FactSynthLock.model_validate(data)
