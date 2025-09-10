from __future__ import annotations
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from app.core.factsynth_lock import FactSynthLock
from app.services.retriever import select_retriever, Retriever
from app.services.evaluator import evaluate_claim

router = APIRouter()

class VerifyRequest(BaseModel):
    claim: str = Field(max_length=1000)
    locale: str
    max_sources: int = Field(default=10, ge=1, le=50)
    allow_untrusted: bool = False

async def get_retriever() -> Retriever:
    return select_retriever()

@router.post("/v1/verify", response_model=FactSynthLock)
async def post_verify(body: VerifyRequest,
                      x_api_key: Optional[str] = Header(default=None),
                      retriever: Retriever = Depends(get_retriever)):
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")
    result = await evaluate_claim(
        claim=body.claim, locale=body.locale,
        retriever=retriever, max_sources=body.max_sources,
        allow_untrusted=body.allow_untrusted
    )
    return result
