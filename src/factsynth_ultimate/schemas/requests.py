from __future__ import annotations

from typing import Annotated, List, Optional

from pydantic import BaseModel, Field


StrippedNonEmpty = Annotated[str, Field(strip_whitespace=True, min_length=1)]
NonNegativeStr = Annotated[str, Field(strip_whitespace=True, min_length=0)]
LimitedInt = Annotated[int, Field(ge=1, le=1000)]
LargeInt = Annotated[int, Field(ge=1, le=10000)]


class IntentReq(BaseModel):
    intent: StrippedNonEmpty
    length: LimitedInt = 100

class ScoreReq(BaseModel):
    text: NonNegativeStr = ""
    targets: Optional[List[StrippedNonEmpty]] = None
    callback_url: Optional[str] = None

class ScoreBatchReq(BaseModel):
    items: List[ScoreReq] = Field(default_factory=list)
    callback_url: Optional[str] = None
    limit: LargeInt = 1000  # soft guard

class GLRTPMReq(BaseModel):
    text: NonNegativeStr = ""
    callback_url: Optional[str] = None
