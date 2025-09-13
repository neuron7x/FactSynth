from pydantic import BaseModel


class RetrievedSource(BaseModel):
    url: str
    title: str | None = None
    snippet: str | None = None
    score: float = 0.0


class Retriever:
    async def retrieve(self, query: str, *, k: int = 5) -> list[RetrievedSource]:
        return []
