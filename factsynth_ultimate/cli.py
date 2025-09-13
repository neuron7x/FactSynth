import asyncio

import typer

from .infra.db import async_session, init_db
from .infra.repository import Repo

app = typer.Typer(help="FactSynth CLI")


@app.command()
def init() -> None:
    asyncio.run(init_db())
    typer.echo("db initialized")


@app.command()
def claim(text: str) -> None:
    async def _run() -> None:
        async with async_session() as s:  # type: ignore[name-defined]
            repo = Repo(s)
            c = await repo.create_claim(text)
            typer.echo(f"claim #{c.id}: {c.text}")

    asyncio.run(_run())


if __name__ == "__main__":
    app()
