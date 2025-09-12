"""Legacy schemas retained for backwards compatibility."""

from __future__ import annotations

from pydantic import BaseModel


class IntentReq(BaseModel):
    """Request body for intent reflection."""

    intent: str
    length: int = 100


class ScoreRequest(BaseModel):
    """Simple scoring request."""

    text: str | None = None
    targets: list[str] | None = None


class ScoreResponse(BaseModel):
    """Container for a numeric score."""

    score: float


class StreamRequest(BaseModel):
    """Request body for streaming previews."""

    text: str | None = None


class GLRTPMRequest(BaseModel):
    """GLRTPM pipeline request."""

    text: str | None = None
