import asyncio

import yaml

from factsynth_ultimate.domain.service import verify_claim
from factsynth_ultimate.infra.db import async_session, init_db
from factsynth_ultimate.infra.repository import Repo
from factsynth_ultimate.plugins.wiki import WikiRetriever


async def _run():
    await init_db()
    with open("golden/cases.yaml", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    async with async_session() as s:  # type: ignore[name-defined]
        repo = Repo(s)
        for case in cases:
            c = await repo.create_claim(case["claim"])
            c = await verify_claim(s, c, [WikiRetriever()])
            if (c.score or 0.0) < case["expected_min_score"]:
                raise AssertionError(case["id"])
    print("golden: ok")


if __name__ == "__main__":
    asyncio.run(_run())
