"""Pydantic models describing a FactSynth lock document.

A lock bundles the final verdict of a claim evaluation together with the
evidence used to reach it.  The models defined here are strict - unknown
fields are rejected to ensure the contract stays stable.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _StrictModel(BaseModel):
    """Base model forbidding unknown fields."""

    model_config = ConfigDict(extra="forbid")


class Decision(str, Enum):
    """Possible outcomes of a claim evaluation."""

    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    MIXED = "mixed"
    NOT_ENOUGH_EVIDENCE = "not_enough_evidence"
    NOT_A_FACT = "not_a_fact"
    # Deprecated aliases preserved for backward compatibility
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_PROVABLE = "not_provable"


class Verdict(_StrictModel):
    """Outcome of the claim evaluation."""

    decision: Decision = Field(..., description="Assessment of the claim")
    confidence: float | None = Field(
        None,
        ge=0,
        le=1,
        description="Optional confidence score in range [0, 1]",
    )

    @field_validator("decision", mode="after")
    @classmethod
    def _normalize_legacy(cls, v: Decision) -> Decision:
        mapping = {
            Decision.SUPPORTED: Decision.CONFIRMED,
            Decision.PARTIALLY_SUPPORTED: Decision.MIXED,
            Decision.NOT_PROVABLE: Decision.NOT_ENOUGH_EVIDENCE,
        }
        return mapping.get(v, v)


class Evidence(_StrictModel):
    """A single piece of evidence supporting the verdict."""

    source_id: str = Field(
        ..., min_length=1, description="Unique identifier of the ingested source"
    )
    source: str = Field(..., min_length=1, description="Identifier or URL of the source")
    content: str = Field(..., min_length=1, description="Excerpt taken from the source")


class FactSynthLock(_StrictModel):
    """Container bundling verdict and evidence."""

    verdict: Verdict
    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Evidence items underpinning the verdict",
    )

    @field_validator("evidence")
    @classmethod
    def _require_evidence(cls, v: list[Evidence]) -> list[Evidence]:
        if not v:
            raise ValueError("evidence must not be empty")
        return v


__all__ = ["Decision", "Evidence", "FactSynthLock", "Verdict"]
