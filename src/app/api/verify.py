from __future__ import annotations

from threading import Lock

from fastapi import APIRouter, Depends

from ..services.evaluator import evaluate_claim

FactSynthLock = Lock()

api = APIRouter()


@api.post("/verify")
def verify(result: dict = Depends(evaluate_claim)) -> dict:  # noqa: B008
    """Verify a claim by delegating to :func:`evaluate_claim`.

    The evaluation is resolved via FastAPI's dependency injection. The exported
    ``FactSynthLock`` can be used by callers wishing to guard concurrent access
    to evaluation resources.
    """
    return result
