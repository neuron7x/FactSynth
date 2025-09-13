from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlmodel.ext.asyncio.session import AsyncSession

from ..domain.service import verify_claim
from ..infra.db import get_session
from ..infra.repository import Repo
from ..plugins.wiki import WikiRetriever

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/claims", tags=["claims"])


class ClaimIn(BaseModel):
    text: str


class ClaimOut(BaseModel):
    id: int
    text: str
    status: str
    verdict: str | None = None
    score: float | None = None


@router.post("", response_model=ClaimOut)
@limiter.limit("30/minute")
async def create_claim(
    request: Request,
    body: ClaimIn,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ClaimOut:
    repo = Repo(session)
    c = await repo.create_claim(body.text)
    return ClaimOut(id=c.id, text=c.text, status=c.status, verdict=c.verdict, score=c.score)


@router.post("/{claim_id}/verify", response_model=ClaimOut)
@limiter.limit("15/minute")
async def verify(
    request: Request,
    claim_id: int,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ClaimOut:
    repo = Repo(session)
    c = await repo.get_claim(claim_id)
    if c is None:
        raise HTTPException(status_code=404, detail="not found")
    c = await verify_claim(session, c, [WikiRetriever()])
    return ClaimOut(id=c.id, text=c.text, status=c.status, verdict=c.verdict, score=c.score)
