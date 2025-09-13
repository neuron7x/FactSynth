from sqlmodel.ext.asyncio.session import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from ..infra.repository import Repo
from ..plugins.base import RetrievedSource, Retriever
from .models import Claim, ClaimStatus, Source


def _score(collected: list[RetrievedSource]) -> float:
    if not collected:
        return 0.0
    s = sum(max(0.0, r.score) for r in collected)
    return min(1.0, s / max(1, len(collected)))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4))  # type: ignore[misc]
async def verify_claim(session: AsyncSession, claim: Claim, retrievers: list[Retriever]) -> Claim:
    repo = Repo(session)
    collected: list[RetrievedSource] = []
    for r in retrievers:
        collected.extend(await r.retrieve(claim.text, k=5))
    sources = [Source(url=i.url, title=i.title, snippet=i.snippet) for i in collected]
    if sources:
        await repo.add_sources(claim, sources)
        claim.status = ClaimStatus.verified if len(sources) >= 1 else ClaimStatus.pending
        claim.verdict = "heuristic"
        claim.score = _score(collected)
        session.add(claim)
        await session.commit()
        await session.refresh(claim)
    return claim
