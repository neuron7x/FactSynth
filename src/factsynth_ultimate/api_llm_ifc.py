from fastapi import APIRouter
from pydantic import BaseModel, Field

from .llm_ifc.arbitrator import Candidate, choose

router = APIRouter(prefix="/v1/llmifc", tags=["llm-ifc"])


class Cand(BaseModel):
    model: str
    quality: float = Field(ge=0, le=1)
    context: float = Field(ge=0, le=1)
    text: str


class ArbReq(BaseModel):
    candidates: list[Cand]
    w1: float = 0.5
    w2: float = 0.5


@router.post("/arbitrate")
def arbitrate(req: ArbReq) -> dict:
    cands = [Candidate(**c.dict()) for c in req.candidates]
    return choose(cands, req.w1, req.w2)
