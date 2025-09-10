from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class QualityBlock:
    """Human-assessed quality information for a document."""

    score: float
    reviewer: str
    notes: str = ""


@dataclass
class ProvenanceBlock:
    """Provenance metadata describing the source of a document."""

    source: str
    url: str | None = None
    license: str | None = None


@dataclass
class FactSynthLock:
    """Container bundling quality and provenance information."""

    quality: List[QualityBlock] = field(default_factory=list)
    provenance: List[ProvenanceBlock] = field(default_factory=list)
