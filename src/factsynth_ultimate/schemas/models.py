from __future__ import annotations

from pydantic import BaseModel


class IntentReq(BaseModel):
    intent: str
    length: int = 100


class ScoreRequest(BaseModel):
    text: str | None = None
    targets: list[str] | None = None


class ScoreResponse(BaseModel):
    score: float


class StreamRequest(BaseModel):
    text: str | None = None


class GLRTPMRequest(BaseModel):
    text: str | None = None
