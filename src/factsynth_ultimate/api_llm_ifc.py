
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict
from .llm_ifc.arbitrator import Candidate, choose

router = APIRouter(prefix="/v1/llmifc", tags=["llm-ifc"])

class Cand(BaseModel):
    model: str
    quality: float = Field(ge=0, le=1)
    context: float = Field(ge=0, le=1)
    text: str

class ArbReq(BaseModel):
    candidates: List[Cand]
    w1: float = 0.5
    w2: float = 0.5

@router.post("/arbitrate")
def arbitrate(req: ArbReq)->Dict:
    cands = [Candidate(**c.dict()) for c in req.candidates]
    return choose(cands, req.w1, req.w2)
