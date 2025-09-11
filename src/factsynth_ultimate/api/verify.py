from __future__ import annotations

from fastapi import APIRouter

from ..core.factsynth_lock import FactSynthLock
from ..services.evaluator import evaluate_claim
from .models import VerifyRequest

api = APIRouter()


@api.post("/verify", response_model=FactSynthLock)
def verify(req: VerifyRequest) -> FactSynthLock:
    """Verify a claim and return the provided lock."""

    evaluate_claim(req.claim)
    return req.lock
