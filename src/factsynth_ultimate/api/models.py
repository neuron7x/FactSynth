"""Pydantic models used by the public API."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from ..core.factsynth_lock import FactSynthLock


RegionCode = Annotated[
    str,
    Field(pattern=r"^[A-Z]{2}$", description="ISO 3166-1 alpha-2 region code"),
]
LanguageCode = Annotated[
    str,
    Field(pattern=r"^[a-z]{2}$", description="ISO 639-1 language code"),
]


class TimeRange(BaseModel):
    """Time window for which the claim should hold."""

    start: datetime = Field(..., description="ISO 8601 start timestamp")
    end: datetime = Field(..., description="ISO 8601 end timestamp")

    @field_validator("end")
    @classmethod
    def _end_after_start(cls, v: datetime, info) -> datetime:
        start = info.data.get("start")
        if start and v < start:
            raise ValueError("end must not be before start")
        return v


class VerifyRequest(BaseModel):
    """Request model for the verification endpoint."""

    claim: str
    region: RegionCode
    language: LanguageCode
    time_range: TimeRange
    lock: FactSynthLock


# Export the request and lock models for use in routers
__all__ = ["FactSynthLock", "VerifyRequest", "TimeRange"]
