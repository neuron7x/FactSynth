from __future__ import annotations
import json, os, re, httpx
from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class RetrievedDoc:
    id: str
    title: str
    url: str
    date: str
    snippet: str
    content: str
    relevance: float

class Retriever:
    async def search(self, query: str, k: int = 10) -> List[RetrievedDoc]: ...
    async def close(self): ...

class LocalFixtureRetriever(Retriever):
    def __init__(self, path: str = "tests/fixtures/index.json"):
        self.path = path
        with open(self.path, "r", encoding="utf-8") as f:
            self.idx = json.load(f)
    async def search(self, query: str, k: int = 10) -> List[RetrievedDoc]:
        hits: List[RetrievedDoc] = []
        q = query.lower()
        translations = {
            "мікросерв": "microservices",
            "вакцин": "vaccine",
            "мікрочіп": "microchip",
        }
        for ua,en in translations.items():
            if ua in q:
                q += " " + en
        for j in self.idx:
            score = sum(q.count(w) for w in re.findall(r"\w+", (j["title"]+j["content"]).lower()))
            if score == 0: continue
            hits.append(RetrievedDoc(
                id=j["id"], title=j["title"], url=j["url"], date=j["date"], snippet=j["snippet"],
                content=j["content"], relevance=min(1.0, 0.1 + score/50.0)
            ))
        hits.sort(key=lambda d:(d.relevance, d.date), reverse=True)
        return hits[:k]
    async def close(self): ...

class BingWebRetriever(Retriever):
    def __init__(self, api_key_env: str = "BING_API_KEY"):
        self.key = os.getenv(api_key_env)
        self.client = httpx.AsyncClient(timeout=20)
    async def search(self, query: str, k: int = 10) -> List[RetrievedDoc]:
        if not self.key:
            return []
        r = await self.client.get(
            "https://api.bing.microsoft.com/v7.0/search",
            params={"q": query, "count": k, "mkt": "en-US"},
            headers={"Ocp-Apim-Subscription-Key": self.key},
        )
        r.raise_for_status()
        data = r.json()
        docs: List[RetrievedDoc] = []
        for i, w in enumerate(data.get("webPages", {}).get("value", [])):
            date = w.get("dateLastCrawled") or datetime.utcnow().date().isoformat()
            docs.append(RetrievedDoc(
                id=str(i+1), title=w.get("name",""), url=w["url"], date=date,
                snippet=w.get("snippet",""), content=w.get("snippet",""),
                relevance=min(1.0, 0.5)
            ))
        return docs
    async def close(self):
        await self.client.aclose()

def select_retriever() -> Retriever:
    # Offline-first for tests; online if key present
    if os.getenv("BING_API_KEY"):
        return BingWebRetriever()
    return LocalFixtureRetriever()
