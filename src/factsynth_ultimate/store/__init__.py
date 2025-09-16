"""Storage backends and helpers used across the service."""

from __future__ import annotations

from .base import (
    STORE_ACTIVE_BACKEND,
    STORE_CONNECT_ATTEMPTS,
    STORE_CONNECT_FAILURES,
    STORE_CONNECT_RETRIES,
    STORE_SWITCHES,
    StoreFactory,
)
from .memory import MemoryStore
from .redis import check_health

__all__ = [
    "MemoryStore",
    "STORE_ACTIVE_BACKEND",
    "STORE_CONNECT_ATTEMPTS",
    "STORE_CONNECT_FAILURES",
    "STORE_CONNECT_RETRIES",
    "STORE_SWITCHES",
    "StoreFactory",
    "check_health",
]
