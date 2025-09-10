from __future__ import annotations
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Literal

class Verdict(BaseModel):
    status: Literal["SUPPORTED","REFUTED","UNCLEAR","OUT_OF_SCOPE","ERROR"]
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str = Field(max_length=300)

class Citation(BaseModel):
    id: str
    source: str
    snippet: str = Field(max_length=500)
    relevance: float = Field(ge=0.0, le=1.0)
    date: str
    url: HttpUrl

class SourceSynthesis(BaseModel):
    key_findings: str = Field(max_length=1000)
    citations: List[Citation]

class Traceability(BaseModel):
    retrieval_query: str
    justification_steps: List[str]
    assumptions: List[str] = []

class Recommendations(BaseModel):
    next_query_suggestion: str
    gaps_identified: List[str] = []
    manual_review: bool = False

class FactSynthLock(BaseModel):
    verdict: Verdict
    source_synthesis: SourceSynthesis
    traceability: Traceability
    recommendations: Recommendations

API_COMPATIBILITY_GUARD = "Do not change FactSynth runtime API"
