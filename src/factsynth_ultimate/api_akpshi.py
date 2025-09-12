"""AKP-SHI verification API endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .akpshi.metrics import fcr, pfi, rmse

router = APIRouter(prefix="/v1/akpshi", tags=["akp-shi"])


class VerifyReq(BaseModel):
    """Payload for prediction verification metrics."""

    y: list[float]
    yhat: list[float]
    confirmed: int = Field(ge=0)
    total: int = Field(ge=1)
    pfi_levels: Optional[list[float]] = None


@router.post("/verify")
def verify(req: VerifyReq) -> dict[str, float]:
    """Return RMSE, FCR and optionally PFI for provided series."""

    out: dict[str, float] = {
        "rmse": rmse(req.y, req.yhat),
        "fcr": fcr(req.confirmed, req.total),
    }
    if req.pfi_levels is not None:
        out["pfi"] = pfi(req.pfi_levels)
    return out
