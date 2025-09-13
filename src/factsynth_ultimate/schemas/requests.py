"""Primary request models used by the API endpoints."""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated

import pycountry
from pydantic import BaseModel, Field, field_validator, model_validator

StrippedNonEmpty = Annotated[str, Field(strip_whitespace=True, min_length=1)]
NonNegativeStr = Annotated[str, Field(strip_whitespace=True, min_length=0)]
LimitedInt = Annotated[int, Field(ge=1, le=1000)]
LargeInt = Annotated[int, Field(ge=1, le=10000)]
Percent = Annotated[float, Field(ge=0.0, le=1.0)]

ISO_DATE = r"\d{4}-\d{2}-\d{2}"
ISO_RANGE_PATTERN = re.compile(rf"^{ISO_DATE}/{ISO_DATE}$")

COUNTRY_CODES = {c.alpha_2 for c in pycountry.countries}
LANGUAGE_CODES = {lang.alpha_2 for lang in pycountry.languages if hasattr(lang, 'alpha_2')}


class ExplicitTimeRange(BaseModel):
    start: Annotated[date, Field(description="ISO 8601 start date")]
    end: Annotated[date, Field(description="ISO 8601 end date")]

    @model_validator(mode="after")
    def check_order(self) -> ExplicitTimeRange:
        if self.end < self.start:
            raise ValueError("end must not be before start")
        return self


TimeRangeStr = Annotated[str, Field(pattern=ISO_RANGE_PATTERN.pattern)]
TimeRange = TimeRangeStr | ExplicitTimeRange


class DomainMetadata(BaseModel):
    """Domain attributes describing region, language and time span."""

    region: Annotated[str, Field(pattern="^[A-Z]{2}$", description="ISO 3166-1 alpha-2 code")]
    language: Annotated[str, Field(pattern="^[a-z]{2}$", description="ISO 639-1 code")]
    time_range: TimeRange

    @field_validator("region", mode="before")
    def normalise_region(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.upper()
        return v

    @field_validator("language", mode="before")
    def normalise_language(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.lower()
        return v

    @field_validator("region")
    def validate_region(cls, v: str) -> str:
        if v not in COUNTRY_CODES:
            raise ValueError("invalid ISO 3166-1 alpha-2 region code")
        return v

    @field_validator("language")
    def validate_language(cls, v: str) -> str:
        if v not in LANGUAGE_CODES:
            raise ValueError("invalid ISO 639-1 language code")
        return v


class IntentReq(BaseModel):
    """Intent reflection request payload."""

    intent: StrippedNonEmpty
    length: LimitedInt = 100


class ScoreReq(BaseModel):
    """Scoring request payload."""

    text: NonNegativeStr = ""
    targets: list[StrippedNonEmpty] | None = None
    callback_url: str | None = None
    domain: DomainMetadata | None = None


class ScoreBatchReq(BaseModel):
    """Batch scoring request."""

    items: list[ScoreReq] = Field(default_factory=list)
    callback_url: str | None = None
    limit: LargeInt = 1000  # soft guard


class GLRTPMReq(BaseModel):
    """Request to run the GLRTPM pipeline."""

    text: NonNegativeStr = ""
    callback_url: str | None = None


class GenerateReq(BaseModel):
    """Request body for deterministic text generation."""

    text: NonNegativeStr = ""
    seed: int | None = None


class FeedbackReq(BaseModel):
    """User feedback metrics payload."""

    explanation_satisfaction: Percent
    citation_precision: Percent
