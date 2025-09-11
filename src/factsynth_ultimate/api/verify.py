from __future__ import annotations

from fastapi import APIRouter, Depends

from ..core.factsynth_lock import FactSynthLock
from ..services.evaluator import evaluate_claim

api = APIRouter()


@api.post("/verify", response_model=FactSynthLock)
def verify(lock: FactSynthLock, _result: dict = Depends(evaluate_claim)) -> FactSynthLock:  # noqa: B008
    """Verify a claim by delegating to :func:`evaluate_claim`.

    The evaluation is resolved via FastAPI's dependency injection. The supplied
    ``FactSynthLock`` document is validated and returned.
    """
    return lock
