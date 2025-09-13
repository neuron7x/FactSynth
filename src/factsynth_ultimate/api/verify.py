"""Expose a simple verification endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from ..services.evaluator import evaluate_claim
from .models import FactSynthLock, VerifyRequest

api = APIRouter()


@api.post("/verify", response_model=FactSynthLock)
def verify(req: VerifyRequest) -> FactSynthLock:
    """Verify a claim and return the provided lock."""

    evaluate_claim(
        req.claim,
        region=req.region,
        language=req.language,
        time_range=(req.time_range.start, req.time_range.end),
    )
    return req.lock
