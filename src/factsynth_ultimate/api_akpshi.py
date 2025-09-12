from fastapi import APIRouter
from pydantic import BaseModel, Field

from .akpshi.metrics import fcr, pfi, rmse

router = APIRouter(prefix="/v1/akpshi", tags=["akp-shi"])


class VerifyReq(BaseModel):
    y: list[float]
    yhat: list[float]
    confirmed: int = Field(ge=0)
    total: int = Field(ge=1)
    pfi_levels: list[float] | None = None


@router.post("/verify")
def verify(req: VerifyReq) -> dict:
    out = {
        "rmse": rmse(req.y, req.yhat),
        "fcr": fcr(req.confirmed, req.total),
    }
    if req.pfi_levels is not None:
        out["pfi"] = pfi(req.pfi_levels)
    return out
