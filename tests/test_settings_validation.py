import pytest
from pydantic import ValidationError

from factsynth_ultimate.core.settings import load_settings


def test_invalid_rate_limit_per_minute(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "abc")
    with pytest.raises(ValidationError):
        load_settings()

