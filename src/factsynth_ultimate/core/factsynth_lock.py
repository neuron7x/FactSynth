"""Pydantic models describing a FactSynth lock document.

The original implementation used ``dataclasses``; this module replaces those
structures with Pydantic models that offer validation and serialization
support. The models are intentionally permissive - unknown fields are allowed -
so the schema can evolve without breaking consumers.
"""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field


class Verdict(BaseModel):
    """Outcome of the claim evaluation."""

    decision: str = Field(..., description="Assessment of the claim")
    confidence: float | None = Field(
        None, description="Confidence score for the assessment"
    )

    model_config = ConfigDict(extra="allow")


class Citation(BaseModel):
    """A citation supporting the evaluation."""

    source: str = Field(..., description="Identifier or URL of the source")
    content: str = Field(..., description="Excerpt taken from the source")

    model_config = ConfigDict(extra="allow")


class SourceSynthesis(BaseModel):
    """Synthesis derived from multiple citations."""

    summary: str = Field(..., description="Summary of the gathered sources")
    citations: List[Citation] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class Traceability(BaseModel):
    """Information enabling reproduction of the verdict."""

    steps: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class Recommendations(BaseModel):
    """Follow-up actions suggested by the evaluation."""

    actions: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class QualityReport(BaseModel):
    """Optional quality metrics for the evaluation."""

    metrics: Dict[str, float] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class Provenance(BaseModel):
    """Optional provenance information for sources."""

    sources: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")


class PolicySnapshot(BaseModel):
    """Optional snapshot of policies in effect during evaluation."""

    policies: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class FactSynthLock(BaseModel):
    """Container bundling all FactSynth evaluation artefacts."""

    verdict: Verdict
    source_synthesis: SourceSynthesis
    traceability: Traceability
    recommendations: Recommendations
    quality_report: QualityReport | None = None
    provenance: Provenance | None = None
    policy_snapshot: PolicySnapshot | None = None

    model_config = ConfigDict(extra="allow")


__all__ = [
    "Citation",
    "FactSynthLock",
    "PolicySnapshot",
    "Provenance",
    "QualityReport",
    "Recommendations",
    "SourceSynthesis",
    "Traceability",
    "Verdict",
]

