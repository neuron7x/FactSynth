"""Application settings loaded from the environment."""

from __future__ import annotations

import re
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from factsynth_ultimate.config import ConfigError, load_config

from .rate_limit import RateQuota
from .secrets import read_api_key


def _default_callback_allowed_hosts() -> list[str]:
    try:
        return load_config().CALLBACK_URL_ALLOWED_HOSTS
    except ConfigError:
        return []


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="")

    env: str = Field(default="dev", env="ENV")
    https_redirect: bool = Field(default=False, env="HTTPS_REDIRECT")
    cors_allow_origins: list[str] = Field(
        default_factory=list,
        env=["CORS_ALLOW_ORIGINS", "CORS_ORIGINS"],
        description=(
            "Allowed CORS origins. Defaults to empty list; set explicitly to enable cross-origin access."
        ),
    )
    auth_header_name: str = Field(default="x-api-key", env="AUTH_HEADER_NAME", min_length=1)
    api_key: str = Field(
        default_factory=lambda: read_api_key("API_KEY", "API_KEY_FILE", "change-me", "API_KEY"),
        min_length=1,
    )
    allowed_api_keys: list[str] = Field(default_factory=list, env="ALLOWED_API_KEYS")
    ip_allowlist: list[str] = Field(default_factory=list, env="IP_ALLOWLIST")
    skip_auth_paths: list[str] = Field(
        default_factory=lambda: ["/v1/healthz", "/metrics"], env="SKIP_AUTH_PATHS"
    )
    callback_url_allowed_hosts: list[str] = Field(
        default_factory=_default_callback_allowed_hosts,
        env="CALLBACK_URL_ALLOWED_HOSTS",
    )
    rate_limit_redis_url: str = Field(
        default="redis://localhost:6379/0", env="RATE_LIMIT_REDIS_URL"
    )
    rates_api: RateQuota = Field(default_factory=lambda: RateQuota(60, 1.0), env="RATES_API")
    rates_ip: RateQuota = Field(default_factory=lambda: RateQuota(60, 1.0), env="RATES_IP")
    rates_org: RateQuota = Field(default_factory=lambda: RateQuota(60, 1.0), env="RATES_ORG")
    token_delay: float = Field(default=0.002, env="TOKEN_DELAY", ge=0)
    health_tcp_checks: list[str] = Field(default_factory=list, env="HEALTH_TCP_CHECKS")
    source_store_backend: str = Field(default="memory", env="SOURCE_STORE_BACKEND")
    source_store_ttl_seconds: int | None = Field(default=3600, env="SOURCE_STORE_TTL_SECONDS")
    source_store_redis_url: str | None = Field(default=None, env="SOURCE_STORE_REDIS_URL")

    @field_validator(
        "cors_allow_origins",
        "skip_auth_paths",
        "health_tcp_checks",
        "ip_allowlist",
        "allowed_api_keys",
        "callback_url_allowed_hosts",
        mode="before",
    )
    @classmethod
    def _split_csv(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            if not value:
                return []
            return [item for item in value.split(",") if item]
        return list(value)

    @field_validator("rates_api", "rates_ip", "rates_org", mode="before")
    @classmethod
    def _parse_rate(cls, value: Any) -> RateQuota:
        if value is None:
            return RateQuota(0, 1.0)
        if isinstance(value, RateQuota):
            return value
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return RateQuota(0, 1.0)
            parts = [part for part in re.split(r"[:/,\s]+", raw) if part]
            if len(parts) == 1:
                burst = int(parts[0])
                sustain = 1.0
            elif len(parts) >= 2:
                burst = int(parts[0])
                sustain = float(parts[1])
            else:  # pragma: no cover - defensive guard
                raise ValueError("Invalid rate specification")
            return RateQuota(burst, sustain)
        if isinstance(value, (tuple, list)):
            if len(value) != 2:
                msg = "Rate tuples must contain burst and sustain"
                raise ValueError(msg)
            burst, sustain = value
            return RateQuota(int(burst), float(sustain))
        if isinstance(value, dict):
            burst = value.get("burst")
            sustain = value.get("sustain")
            if burst is None or sustain is None:
                msg = "Rate mappings must define 'burst' and 'sustain'"
                raise ValueError(msg)
            return RateQuota(int(burst), float(sustain))
        msg = f"Unsupported rate configuration: {type(value)!r}"
        raise TypeError(msg)

    @property
    def rate_limit_per_key(self) -> int:
        """Backwards compatible accessor for legacy configuration."""

        return self.rates_api.burst

    @property
    def rate_limit_per_ip(self) -> int:
        """Backwards compatible accessor for legacy configuration."""

        return self.rates_ip.burst

    @property
    def rate_limit_per_org(self) -> int:
        """Backwards compatible accessor for legacy configuration."""

        return self.rates_org.burst


def load_settings() -> Settings:
    """Load settings from environment variables."""

    return Settings()
