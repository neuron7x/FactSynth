from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class VectorMemory:
    def __init__(self):
        self.docs: List[str] = []
        self.vec = TfidfVectorizer()
        self.matrix = None

    def add(self, text: str):
        self.docs.append(text)
        self.matrix = self.vec.fit_transform(self.docs)

    def search(self, query: str, topk: int = 3) -> List[Tuple[int, float, str]]:
        if not self.docs:
            return []
        q = self.vec.transform([query])
        sims = cosine_similarity(q, self.matrix).ravel()
        idx = sims.argsort()[::-1][:topk]
        return [(int(i), float(sims[i]), self.docs[i]) for i in idx]
