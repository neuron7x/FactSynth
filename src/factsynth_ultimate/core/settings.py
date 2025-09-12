"""Application settings loaded from the environment."""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="")

    env: str = Field(default="dev", env="ENV")
    https_redirect: bool = Field(default=False, env="HTTPS_REDIRECT")
    cors_allow_origins: list[str] = Field(
        default=[],
        env="CORS_ALLOW_ORIGINS",
        description="Allowed CORS origins. Defaults to empty list; set explicitly to enable cross-origin access.",
    )
    auth_header_name: str = Field(default="x-api-key", env="AUTH_HEADER_NAME")
    ip_allowlist: list[str] = Field(default_factory=list, env="IP_ALLOWLIST")
    skip_auth_paths: list[str] = Field(
        default_factory=lambda: ["/v1/healthz", "/metrics"], env="SKIP_AUTH_PATHS"
    )
    rate_limit_redis_url: str = Field(env="RATE_LIMIT_REDIS_URL")
    rate_limit_per_key: int = Field(default=120, env="RATE_LIMIT_PER_KEY")
    rate_limit_per_ip: int = Field(default=120, env="RATE_LIMIT_PER_IP")
    rate_limit_per_org: int = Field(default=120, env="RATE_LIMIT_PER_ORG")
    health_tcp_checks: list[str] = Field(default_factory=list, env="HEALTH_TCP_CHECKS")

    @field_validator("cors_allow_origins", "skip_auth_paths", "health_tcp_checks", "ip_allowlist", mode="before")
    @classmethod
    def _split_csv(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            if not value:
                return []
            return [item for item in value.split(",") if item]
        return list(value)


def load_settings() -> Settings:
    """Load settings from environment variables."""

    return Settings()

