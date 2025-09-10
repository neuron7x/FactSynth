import pytest
from pydantic import ValidationError

from factsynth_ultimate.core.settings import Settings, load_settings


@pytest.mark.parametrize(
    "field",
    [
        "cors_allow_origins",
        "skip_auth_paths",
        "ip_allowlist",
        "health_tcp_checks",
    ],
)
def test_csv_fields(field):
    settings = Settings(**{field: "a,b"})
    assert getattr(settings, field) == ["a", "b"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", []),
        ("one", ["one"]),
        ("a, b", ["a", " b"]),
    ],
)
def test_split_csv_edge_cases(raw, expected):
    assert Settings._split_csv(raw) == expected


def test_invalid_rate_limit_per_minute(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "abc")
    with pytest.raises(ValidationError):
        load_settings()

