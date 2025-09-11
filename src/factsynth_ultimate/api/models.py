from __future__ import annotations

from pydantic import BaseModel

from ..core.factsynth_lock import FactSynthLock


class VerifyRequest(BaseModel):
    """Request model for the verification endpoint."""

    claim: str
    lock: FactSynthLock


__all__ = ["VerifyRequest"]
