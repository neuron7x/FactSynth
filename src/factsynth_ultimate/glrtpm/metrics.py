
from typing import Dict, List

def _len(s:str)->int: return len(s or "")

def compute_coherence(*parts:str)->float:
    L = sum(_len(p) for p in parts) or 1
    uniq_tokens = len(set(" ".join(parts).lower().split()))
    return round(uniq_tokens / L * 10.0, 4)

def cluster_density(nodes: List[str])->float:
    total = sum(_len(n) for n in nodes) or 1
    uniq = len(set(" ".join(nodes).lower().split()))
    return round(uniq / total, 4)

def role_contribution(chunks: Dict[str,str])->Dict[str,float]:
    total = sum(_len(v) for v in chunks.values()) or 1
    return {k: round(_len(v)/total, 3) for k,v in chunks.items()}
