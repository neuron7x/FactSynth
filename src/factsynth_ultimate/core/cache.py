from __future__ import annotations

import json
from typing import Any

from .settings import load_settings

try:  # pragma: no cover - optional dependency
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class Cache:
    """Simple cache that can use Redis if configured."""

    def __init__(self, url: str | None, ttl: int) -> None:
        self.ttl = ttl
        if url and redis is not None:
            self._redis = redis.Redis.from_url(url)
            self._store: dict[str, Any] | None = None
        else:
            self._redis = None
            self._store = {}

    def get(self, key: str) -> Any | None:
        if self._redis is not None:
            value = self._redis.get(key)
            if value is not None:
                return json.loads(value)
            return None
        return self._store.get(key) if self._store is not None else None

    def set(self, key: str, value: Any) -> None:
        if self._redis is not None:
            self._redis.setex(key, self.ttl, json.dumps(value))
        elif self._store is not None:
            self._store[key] = value

    def clear(self) -> None:
        if self._redis is not None:
            self._redis.flushdb()
        elif self._store is not None:
            self._store.clear()


_cache: Cache | None = None


def get_cache() -> Cache:
    """Return a singleton cache instance configured from settings."""
    global _cache
    if _cache is None:
        settings = load_settings()
        _cache = Cache(settings.redis_url, settings.cache_ttl)
    return _cache
