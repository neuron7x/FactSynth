"""In-memory storage backend compatible with Redis operations."""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping


class MemoryStore:
    """Minimal async-compatible Redis replacement used for fallbacks."""

    def __init__(self, *, now: Callable[[], float] | None = None) -> None:
        self._data: dict[str, dict[str, str]] = {}
        self._expiry: dict[str, float] = {}
        self._now = now or time.monotonic

    def _current_time(self) -> float:
        return float(self._now())

    def _maybe_expire(self, key: str) -> None:
        deadline = self._expiry.get(key)
        if deadline is not None and self._current_time() >= deadline:
            self._data.pop(key, None)
            self._expiry.pop(key, None)

    async def hgetall(self, key: str) -> dict[str, str]:
        self._maybe_expire(key)
        return self._data.get(key, {}).copy()

    async def hset(self, key: str, mapping: Mapping[str, Any]) -> None:
        self._maybe_expire(key)
        encoded = {str(k): str(v) for k, v in mapping.items()}
        bucket = self._data.setdefault(key, {})
        bucket.update(encoded)

    async def expire(self, key: str, ttl: int) -> None:
        if ttl <= 0:
            self._data.pop(key, None)
            self._expiry.pop(key, None)
        else:
            self._expiry[key] = self._current_time() + float(ttl)

    async def incr(self, key: str) -> int:
        self._maybe_expire(key)
        bucket = self._data.setdefault(key, {})
        value = int(bucket.get("_value", "0")) + 1
        bucket["_value"] = str(value)
        return value

    async def ttl(self, key: str) -> int:
        self._maybe_expire(key)
        if key not in self._data:
            return -2
        deadline = self._expiry.get(key)
        if deadline is None:
            return -1
        remaining = int(deadline - self._current_time())
        return remaining if remaining >= 0 else -2

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)
        self._expiry.pop(key, None)

    async def ping(self) -> bool:  # pragma: no cover - trivial behaviour
        return True
