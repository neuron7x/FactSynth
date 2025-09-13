"""Primary request models used by the API endpoints."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

StrippedNonEmpty = Annotated[str, Field(strip_whitespace=True, min_length=1)]
NonNegativeStr = Annotated[str, Field(strip_whitespace=True, min_length=0)]
LimitedInt = Annotated[int, Field(ge=1, le=1000)]
LargeInt = Annotated[int, Field(ge=1, le=10000)]
Percent = Annotated[float, Field(ge=0.0, le=1.0)]


class IntentReq(BaseModel):
    """Intent reflection request payload."""

    intent: StrippedNonEmpty
    length: LimitedInt = 100


class ScoreReq(BaseModel):
    """Scoring request payload."""

    text: NonNegativeStr = ""
    targets: list[StrippedNonEmpty] | None = None
    callback_url: str | None = None


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
