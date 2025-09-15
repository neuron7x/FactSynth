from __future__ import annotations

import json
import os
import time
from typing import Any

from cachetools import LRUCache

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - redis optional  # noqa: BLE001
    redis = None  # type: ignore

DEFAULT_TTL = int(os.getenv("CACHE_TTL_SEC", "900"))


class MemoryBuffer:
    """Unified cache layer backed by Redis or in-process LRU."""

    def __init__(self, maxsize: int = 2048, ttl: int = DEFAULT_TTL) -> None:
        self.ttl = ttl
        self._lru: LRUCache[str, tuple[float, Any]] = LRUCache(maxsize=maxsize)
        self._r: redis.Redis[str] | None = None
        url = os.getenv("REDIS_URL")
        if url and redis is not None:
            try:
                self._r = redis.Redis.from_url(url, decode_responses=True)
                self._r.ping()
            except Exception:  # noqa: BLE001
                self._r = None

    def _key(self, namespace: str, key: str) -> str:
        return f"fs:{namespace}:{key}"

    def get(self, namespace: str, key: str) -> Any | None:
        k = self._key(namespace, key)
        if self._r:
            value = self._r.get(k)
            return json.loads(value) if value is not None else None
        item = self._lru.get(k)
        if not item:
            return None
        exp, val = item
        if exp < time.time():
            self._lru.pop(k, None)
            return None
        return val

    def set(self, namespace: str, key: str, value: Any, ttl: int | None = None) -> None:
        k = self._key(namespace, key)
        payload = json.dumps(value, ensure_ascii=False)
        t = ttl or self.ttl
        if self._r:
            self._r.set(k, payload, ex=t)
        else:
            self._lru[k] = (time.time() + t, value)

    def delete(self, namespace: str, key: str) -> None:
        k = self._key(namespace, key)
        if self._r:
            self._r.delete(k)
        else:
            self._lru.pop(k, None)
