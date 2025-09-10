from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="")

    env: str = Field(default="dev", env="ENV")
    https_redirect: bool = Field(default=False, env="HTTPS_REDIRECT")
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"], env="CORS_ALLOW_ORIGINS")
    auth_header_name: str = Field(default="x-api-key", env="AUTH_HEADER_NAME")
    ip_allowlist: list[str] = Field(default_factory=list, env="IP_ALLOWLIST")
    skip_auth_paths: list[str] = Field(
        default_factory=lambda: ["/v1/healthz", "/v1/version"], env="SKIP_AUTH_PATHS"
    )
    rate_limit_per_minute: int = Field(default=120, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_bucket_ttl: float = Field(default=300.0, env="RATE_LIMIT_BUCKET_TTL")
    rate_limit_cleanup_interval: float = Field(default=60.0, env="RATE_LIMIT_CLEANUP_INTERVAL")
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
    return Settings()

