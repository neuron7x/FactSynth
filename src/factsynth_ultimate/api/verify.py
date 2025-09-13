"""Expose a simple verification endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from ..services.evaluator import evaluate_claim
from .models import FactSynthLock, VerifyRequest

api = APIRouter()


@api.post("/verify", response_model=FactSynthLock)
def verify(req: VerifyRequest) -> FactSynthLock:
    """Verify a claim and merge evaluation results into the lock."""

    evaluation = evaluate_claim(req.claim)
    lock_data = req.lock.model_dump()

    if verdict := evaluation.get("verdict"):
        lock_data["verdict"] = verdict
    if evidence := evaluation.get("evidence"):
        lock_data["evidence"] = evidence

    return FactSynthLock.model_validate(lock_data)
