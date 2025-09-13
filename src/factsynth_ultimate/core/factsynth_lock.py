"""Pydantic models describing a FactSynth lock document.

The original implementation used ``dataclasses``; this module replaces those
structures with Pydantic models that offer validation and serialization
support. The models enforce a strict schema so the contract remains explicit.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Verdict(BaseModel):
    """Outcome of the claim evaluation."""

    decision: Literal["supported", "refuted", "uncertain"] = Field(
        ..., description="Assessment of the claim"
    )
    confidence: float | None = Field(None, description="Confidence score for the assessment")

    model_config = ConfigDict(extra="forbid")


class Citation(BaseModel):
    """A citation supporting the evaluation."""

    source: str = Field(..., description="Identifier or URL of the source")
    content: str = Field(..., description="Excerpt taken from the source")

    model_config = ConfigDict(extra="forbid")


class SourceSynthesis(BaseModel):
    """Synthesis derived from multiple citations."""

    summary: str = Field(..., description="Summary of the gathered sources")
    citations: list[Citation] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class Traceability(BaseModel):
    """Information enabling reproduction of the verdict."""

    steps: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class Recommendations(BaseModel):
    """Follow-up actions suggested by the evaluation."""

    actions: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class QualityReport(BaseModel):
    """Optional quality metrics for the evaluation."""

    metrics: dict[str, float] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class Provenance(BaseModel):
    """Optional provenance information for sources."""

    sources: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class PolicySnapshot(BaseModel):
    """Optional snapshot of policies in effect during evaluation."""

    policies: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class FactSynthLock(BaseModel):
    """Container bundling all FactSynth evaluation artefacts."""

    verdict: Verdict
    source_synthesis: SourceSynthesis
    traceability: Traceability
    recommendations: Recommendations
    quality_report: QualityReport | None = None
    provenance: Provenance | None = None
    policy_snapshot: PolicySnapshot | None = None

    model_config = ConfigDict(extra="forbid")


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
