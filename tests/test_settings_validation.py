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


def test_cors_allow_origins_default_empty():
    settings = Settings()
    assert settings.cors_allow_origins == []


def test_invalid_rate_limit_per_key(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("RATE_LIMIT_PER_KEY", "abc")
    with pytest.raises(ValidationError):
        load_settings()

