from collections.abc import Sequence
from typing import cast

from sqlmodel.ext.asyncio.session import AsyncSession

from ..domain.models import Claim, ClaimSourceLink, Source


class Repo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_claim(self, text: str) -> Claim:
        c = Claim(text=text)
        self.session.add(c)
        await self.session.commit()
        await self.session.refresh(c)
        return c

    async def get_claim(self, claim_id: int) -> Claim | None:
        return cast(Claim | None, await self.session.get(Claim, claim_id))

    async def add_sources(self, claim: Claim, sources: Sequence[Source]) -> None:
        for s in sources:
            self.session.add(s)
            await self.session.flush()
            self.session.add(ClaimSourceLink(claim_id=claim.id, source_id=s.id))
        await self.session.commit()
