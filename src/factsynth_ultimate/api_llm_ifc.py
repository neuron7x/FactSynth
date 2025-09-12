
"""API endpoints for lightweight LLM inference arbitration."""

from typing import Any, Dict, List, cast

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .llm_ifc.arbitrator import Candidate, choose

router = APIRouter(prefix="/v1/llmifc", tags=["llm-ifc"])


class Cand(BaseModel):
    """Single LLM candidate and its evaluation metrics."""

    model: str
    quality: float = Field(ge=0, le=1)
    context: float = Field(ge=0, le=1)
    text: str


class ArbReq(BaseModel):
    """Request body for arbitration between multiple candidates."""

    candidates: List[Cand]
    w1: float = 0.5
    w2: float = 0.5


@router.post("/arbitrate")
def arbitrate(req: ArbReq) -> Dict[str, Any]:
    """Choose the best candidate based on quality and context weights."""

    cands = [Candidate(**c.dict()) for c in req.candidates]
    return cast(Dict[str, Any], choose(cands, req.w1, req.w2))
