from __future__ import annotations

from threading import Lock
from typing import Any, Iterator

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..core.factsynth_lock import FactSynthLock
from ..services.evaluator import evaluate_claim
from ..services.retriever import LocalFixtureRetriever

fs_lock = Lock()
router = APIRouter()


class VerifyRequest(BaseModel):
    claim: str
    locale: str = "en"
    max_sources: int = 5
    allow_untrusted: bool = False


def build_retriever(req: VerifyRequest) -> Iterator[LocalFixtureRetriever]:  # noqa: ARG001
    retriever = LocalFixtureRetriever([])
    try:
        yield retriever
    finally:
        if hasattr(retriever, "close"):
            retriever.close()


@router.post("/v1/verify", response_model=FactSynthLock)
def verify(
    request: VerifyRequest, retriever: Any = Depends(build_retriever)  # noqa: B008
) -> FactSynthLock:
    """Verify a claim by delegating to :func:`evaluate_claim`."""
    result = evaluate_claim(request.claim, retriever=retriever)
    payload = {k: result.get(k) for k in ("quality", "provenance") if k in result}
    return FactSynthLock(**payload)
