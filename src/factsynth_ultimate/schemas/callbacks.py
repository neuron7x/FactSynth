"""Schemas for managing callback allowlists via API."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CallbackHostRequest(BaseModel):
    """Request payload for adding a single callback host."""

    host: str = Field(description="Hostname to allow for callbacks")

    @field_validator("host")
    @classmethod
    def _normalize(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("host must not be empty")
        return normalized


class CallbackAllowlistSetRequest(BaseModel):
    """Request payload for replacing the callback allowlist."""

    hosts: list[str] = Field(default_factory=list, description="List of allowed callback hosts")

    @field_validator("hosts")
    @classmethod
    def _normalize_hosts(cls, hosts: list[str]) -> list[str]:
        return [host.strip().lower() for host in hosts if host and host.strip()]


class CallbackAllowlistResponse(BaseModel):
    """Response payload describing the configured callback allowlist."""

    hosts: list[str]

