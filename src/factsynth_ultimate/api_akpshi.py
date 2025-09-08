
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from .akpshi.metrics import rmse, fcr, pfi

router = APIRouter(prefix="/v1/akpshi", tags=["akp-shi"])

class VerifyReq(BaseModel):
    y: List[float]
    yhat: List[float]
    confirmed: int = Field(ge=0)
    total: int = Field(ge=1)
    pfi_levels: Optional[List[float]] = None

@router.post("/verify")
def verify(req: VerifyReq)->Dict:
    out = {
        "rmse": rmse(req.y, req.yhat),
        "fcr": fcr(req.confirmed, req.total),
    }
    if req.pfi_levels is not None:
        out["pfi"] = pfi(req.pfi_levels)
    return out
