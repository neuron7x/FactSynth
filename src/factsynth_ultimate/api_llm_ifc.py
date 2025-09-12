
"""LLM inference competition API endpoints."""

from typing import Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .llm_ifc.arbitrator import Candidate, choose

router = APIRouter(prefix="/v1/llmifc", tags=["llm-ifc"])

class Cand(BaseModel):
    """Candidate response supplied to the arbitrator."""

    model: str
    quality: float = Field(ge=0, le=1)
    context: float = Field(ge=0, le=1)
    text: str


class ArbReq(BaseModel):
    """Arbitration request containing model candidates."""

    candidates: List[Cand]
    w1: float = 0.5
    w2: float = 0.5


@router.post("/arbitrate")
def arbitrate(req: ArbReq) -> Dict[str, float | str | None]:
    """Choose the best candidate using weighted scoring."""

    cands = [Candidate(**c.dict()) for c in req.candidates]
    return choose(cands, req.w1, req.w2)
