"""Source metadata store with optional TTL eviction or persistent backend."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Protocol
from uuid import uuid4

import redis

from .settings import load_settings


@dataclass
class SourceMetadata:
    """Metadata associated with an ingested source."""

    url: str
    date: str
    hash: str


class SourceStore(Protocol):
    """Protocol describing store operations."""

    def ingest_source(self, url: str, content: str) -> str: ...

    def get_metadata(self, source_id: str) -> SourceMetadata | None: ...

    def cleanup(self) -> None: ...


class MemorySourceStore:
    """In-memory store with optional TTL support."""

    def __init__(self, ttl: int | None = None):
        self._db: dict[str, tuple[SourceMetadata, datetime | None]] = {}
        self.ttl = ttl

    def ingest_source(self, url: str, content: str) -> str:
        source_id = uuid4().hex
        metadata = SourceMetadata(
            url=url,
            date=datetime.now(UTC).isoformat(),
            hash=sha256(content.encode("utf-8")).hexdigest(),
        )
        expires = datetime.now(UTC) + timedelta(seconds=self.ttl) if self.ttl is not None else None
        self._db[source_id] = (metadata, expires)
        return source_id

    def get_metadata(self, source_id: str) -> SourceMetadata | None:
        item = self._db.get(source_id)
        if not item:
            return None
        metadata, expires = item
        if expires and datetime.now(UTC) >= expires:
            del self._db[source_id]
            return None
        return metadata

    def cleanup(self) -> None:
        if not self.ttl:
            return
        now = datetime.now(UTC)
        expired = [k for k, (_, exp) in self._db.items() if exp and exp <= now]
        for key in expired:
            del self._db[key]


class RedisSourceStore:
    """Redis-backed store relying on Redis for TTL management."""

    def __init__(self, redis_client, ttl: int | None = None):
        self.redis = redis_client
        self.ttl = ttl

    def ingest_source(self, url: str, content: str) -> str:
        source_id = uuid4().hex
        metadata = SourceMetadata(
            url=url,
            date=datetime.now(UTC).isoformat(),
            hash=sha256(content.encode("utf-8")).hexdigest(),
        )
        self.redis.hset(source_id, mapping=metadata.__dict__)
        if self.ttl:
            self.redis.expire(source_id, self.ttl)
        return source_id

    def get_metadata(self, source_id: str) -> SourceMetadata | None:
        data = self.redis.hgetall(source_id)
        if not data:
            return None
        return SourceMetadata(
            url=data[b"url"].decode(),
            date=data[b"date"].decode(),
            hash=data[b"hash"].decode(),
        )

    def cleanup(self) -> None:  # pragma: no cover - Redis handles TTL itself
        return


def _build_store() -> SourceStore:
    settings = load_settings()
    if settings.source_store_backend == "redis":
        client = redis.from_url(settings.source_store_redis_url or "redis://localhost")
        return RedisSourceStore(client, ttl=settings.source_store_ttl_seconds)
    return MemorySourceStore(ttl=settings.source_store_ttl_seconds)


_STORE: SourceStore = _build_store()


def ingest_source(url: str, content: str) -> str:
    """Generate a unique ``source_id`` and persist metadata."""

    return _STORE.ingest_source(url, content)


def get_metadata(source_id: str) -> SourceMetadata | None:
    """Return stored metadata for ``source_id`` if present."""

    return _STORE.get_metadata(source_id)


def cleanup_expired_entries() -> None:
    """Remove expired entries for in-memory backend."""

    _STORE.cleanup()


__all__ = [
    "MemorySourceStore",
    "RedisSourceStore",
    "SourceMetadata",
    "cleanup_expired_entries",
    "get_metadata",
    "ingest_source",
]
