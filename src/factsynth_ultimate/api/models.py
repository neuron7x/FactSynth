"""Pydantic models used by the public API."""

from __future__ import annotations

from pydantic import BaseModel

from ..core.factsynth_lock import FactSynthLock


class VerifyRequest(BaseModel):
    """Request model for the verification endpoint."""

    claim: str
    lock: FactSynthLock


# Export the request and lock models for use in routers
__all__ = ["FactSynthLock", "VerifyRequest"]
