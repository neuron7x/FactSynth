"""Application settings loaded from the environment."""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .secrets import read_api_key


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
    callback_url_allowed_hosts: str = Field(default="", env="CALLBACK_URL_ALLOWED_HOSTS")
    rate_limit_redis_url: str = Field(
        default="redis://localhost:6379/0", env="RATE_LIMIT_REDIS_URL"
    )
    rate_limit_per_key: int = Field(default=120, env="RATE_LIMIT_PER_KEY", ge=0)
    rate_limit_per_ip: int = Field(default=120, env="RATE_LIMIT_PER_IP", ge=0)
    rate_limit_per_org: int = Field(default=120, env="RATE_LIMIT_PER_ORG", ge=0)
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
        mode="before",
    )
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
