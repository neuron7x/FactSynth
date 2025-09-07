from __future__ import annotations
from pydantic import BaseModel

class IntentReq(BaseModel):
    intent: str
    length: int = 100
