"""Centralized application configuration."""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .secrets import read_api_key


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="")

    auth_header_name: str = Field(default="x-api-key", env="AUTH_HEADER_NAME")
    api_key: str = Field(
        default_factory=lambda: read_api_key("API_KEY", "API_KEY_FILE", "change-me", "API_KEY")
    )
    allowed_api_keys: list[str] = Field(default_factory=list, env="ALLOWED_API_KEYS")
    ip_allowlist: list[str] = Field(default_factory=list, env="IP_ALLOWLIST")
    cors_origins: list[str] = Field(default_factory=list, env="CORS_ORIGINS")
    rate_limit_redis_url: str = Field(
        default="redis://localhost:6379/0", env="RATE_LIMIT_REDIS_URL"
    )
    rate_limit_per_key: int = Field(default=120, env="RATE_LIMIT_PER_KEY")
    rate_limit_per_ip: int = Field(default=120, env="RATE_LIMIT_PER_IP")
    rate_limit_per_org: int = Field(default=120, env="RATE_LIMIT_PER_ORG")

    @field_validator("ip_allowlist", "cors_origins", "allowed_api_keys", mode="before")
    @classmethod
    def _split_csv(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            if not value:
                return []
            return [item for item in value.split(",") if item]
        return list(value)

    @field_validator("auth_header_name")
    @classmethod
    def _non_empty_header(cls, value: str) -> str:
        if not value:
            raise ValueError("AUTH_HEADER_NAME must not be empty")
        return value

    @field_validator("api_key")
    @classmethod
    def _validate_api_key(cls, value: str) -> str:
        if not value:
            raise ValueError("API_KEY must not be empty")
        return value

    @field_validator("rate_limit_per_key", "rate_limit_per_ip", "rate_limit_per_org")
    @classmethod
    def _non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Rate limits must be non-negative")
        return value


def load_config() -> Config:
    """Load configuration from environment variables."""

    return Config()
