"""Endpoints for AKP-SHI metrics."""

from typing import Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .akpshi.metrics import fcr, pfi, rmse

router = APIRouter(prefix="/v1/akpshi", tags=["akp-shi"])

class VerifyReq(BaseModel):
    """Payload for :func:`verify` containing predictions and outcomes."""

    y: List[float]
    yhat: List[float]
    confirmed: int = Field(ge=0)
    total: int = Field(ge=1)
    pfi_levels: Optional[List[float]] = None


@router.post("/verify")
def verify(req: VerifyReq) -> Dict[str, float]:
    """Compute RMSE, FCR and optionally PFI metrics."""

    out: Dict[str, float] = {
        "rmse": rmse(req.y, req.yhat),
        "fcr": fcr(req.confirmed, req.total),
    }
    if req.pfi_levels is not None:
        out["pfi"] = pfi(req.pfi_levels)
    return out
