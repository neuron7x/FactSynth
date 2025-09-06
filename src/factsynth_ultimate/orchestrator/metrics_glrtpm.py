from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def coherence(docs: List[str]) -> float:
    if len(docs) < 2: return 1.0
    vec = TfidfVectorizer(); X = vec.fit_transform(docs); S = cosine_similarity(X)
    n = S.shape[0]; return float((S.sum() - n) / (n*(n-1)))

def diversity(docs: List[str]) -> float:
    if len(docs) < 2: return 0.0
    vec = TfidfVectorizer(); X = vec.fit_transform(docs); S = cosine_similarity(X)
    return float(1.0 - S[np.triu_indices(S.shape[0], k=1)].mean())

def contradiction_rate(thesis_blocks: List[str], counter_blocks: List[str]) -> float:
    if not thesis_blocks or not counter_blocks: return 0.0
    vec = TfidfVectorizer(); X = vec.fit_transform(thesis_blocks + counter_blocks); n = len(thesis_blocks)
    A, B = X[:n], X[n:]; S = cosine_similarity(A, B).mean()
    return float(1.0 - S)

def acceptance(coh: float, div: float, contra: float) -> Dict[str, float]:
    return {"coherence": coh, "diversity": div, "contradiction": contra}
