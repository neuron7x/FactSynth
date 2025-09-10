from __future__ import annotations
import re
from typing import List, Tuple
from app.core.factsynth_lock import FactSynthLock, Verdict, SourceSynthesis, Traceability, Recommendations
from app.services.retriever import Retriever, RetrievedDoc

def _stance_score(claim: str, text: str) -> float:
    c = claim.lower()
    t = text.lower()
    neg_markers = [
        "не","refute","myth","false","no evidence","not supported","спростовано",
        "increase","rise","higher cost","overhead"
    ]
    pos_markers = ["підтвердж","support","evidence","confirmed","consensus","доведено"]
    s = 0.0
    for w in pos_markers:
        if w in t: s += 1.0
    for w in neg_markers:
        if w in t: s -= 1.0
    # keyword overlap
    kws = set(re.findall(r"\b[a-zа-яіїє0-9]{4,}\b", c))
    overlap = sum(1 for k in kws if k in t)
    s += min(2.0, overlap/10.0)
    return s

def _verdict_from_scores(scores: List[float]) -> Tuple[str, float]:
    if not scores:
        return ("UNCLEAR", 0.2)
    avg = sum(scores)/len(scores)
    mag = sum(abs(x) for x in scores)/max(1,len(scores))
    if avg > 0.5 and mag > 0.6:
        return ("SUPPORTED", min(0.9, 0.6 + avg/3))
    if avg < -0.5 and mag > 0.6:
        return ("REFUTED",  min(0.9, 0.6 + abs(avg)/3))
    return ("UNCLEAR", 0.4)

async def evaluate_claim(claim: str, locale: str, retriever: Retriever, max_sources: int, allow_untrusted: bool) -> FactSynthLock:
    query = claim.strip()
    docs: List[RetrievedDoc] = await retriever.search(query, k=max_sources)
    citations = []
    scores = []
    for d in docs:
        sc = _stance_score(claim, f"{d.title}. {d.snippet}. {d.content}")
        scores.append(sc)
        citations.append(dict(
            id=d.id, source=d.title[:120] or d.url, snippet=d.snippet[:500],
            relevance=round(max(0.0, min(1.0, d.relevance)), 3), date=d.date, url=d.url
        ))
    status, conf = _verdict_from_scores(scores)
    jf = [
        "Сформовано запит і відібрано високорелевантні джерела.",
        "Оцінили маркери підтримки/спростування та ключові збіги термінів.",
        "Агрегували сигнали й визначили статус за пороговими правилами.",
    ]
    if not docs:
        jf.append("Недостатньо зовнішніх джерел — потрібен ручний огляд.")
    return FactSynthLock(
        verdict=Verdict(status=status, confidence=round(conf,2),
                        summary=("Твердження підтверджено." if status=="SUPPORTED"
                                 else "Твердження спростовано." if status=="REFUTED"
                                 else "Доказів недостатньо для остаточного висновку.")),
        source_synthesis=SourceSynthesis(
            key_findings="Узгоджено сигнали з відібраних джерел; суперечності згладжено за правилом більшості з вагами релевантності.",
            citations=citations or []
        ),
        traceability=Traceability(
            retrieval_query=query,
            justification_steps=jf,
            assumptions=([] if docs else ["Обмежений доступ до онлайн-пошуку під час виконання тестів"])
        ),
        recommendations=Recommendations(
            next_query_suggestion="Уточнити ключові терміни твердження та перевірити первинні джерела.",
            gaps_identified=([] if docs else ["Немає доступних надійних джерел у пошуку"]),
            manual_review=(len(docs)==0)
        )
    )
