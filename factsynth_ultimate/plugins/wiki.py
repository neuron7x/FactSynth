from .base import RetrievedSource, Retriever


class WikiRetriever(Retriever):
    async def retrieve(self, query: str, *, k: int = 5) -> list[RetrievedSource]:
        return []  # stub for later web integration
