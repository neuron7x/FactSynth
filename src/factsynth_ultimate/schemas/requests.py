from __future__ import annotations
from pydantic import BaseModel, Field, conint, constr, field_validator
from typing import List, Optional

class IntentReq(BaseModel):
    intent: constr(strip_whitespace=True, min_length=1)  # noqa: F722
    length: conint(ge=1, le=1000) = 100  # noqa: F722

class ScoreReq(BaseModel):
    text: constr(strip_whitespace=True, min_length=0) = ""  # noqa: F722
    targets: Optional[List[constr(strip_whitespace=True, min_length=1)]] = None  # noqa: F722
    callback_url: Optional[str] = None

class ScoreBatchReq(BaseModel):
    items: List[ScoreReq] = Field(default_factory=list)
    callback_url: Optional[str] = None
    limit: conint(ge=1, le=10000) = 1000  # soft guard

class GLRTPMReq(BaseModel):
    text: constr(strip_whitespace=True, min_length=0) = ""  # noqa: F722
    callback_url: Optional[str] = None
