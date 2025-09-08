from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, conint, constr


class IntentReq(BaseModel):
    intent: constr(strip_whitespace=True, min_length=1)
    length: conint(ge=1, le=1000) = 100

class ScoreReq(BaseModel):
    text: constr(strip_whitespace=True, min_length=0) = ""
    targets: Optional[List[constr(strip_whitespace=True, min_length=1)]] = None
    callback_url: Optional[str] = None

class ScoreBatchReq(BaseModel):
    items: List[ScoreReq] = Field(default_factory=list)
    callback_url: Optional[str] = None
    limit: conint(ge=1, le=10000) = 1000  # soft guard

class GLRTPMReq(BaseModel):
    text: constr(strip_whitespace=True, min_length=0) = ""
    callback_url: Optional[str] = None
