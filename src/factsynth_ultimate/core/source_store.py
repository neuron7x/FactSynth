"""Source metadata store with optional TTL eviction or persistent backend."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any, Protocol, cast
from uuid import uuid4

import redis

from ..store import StoreFactory
from .settings import load_settings


@dataclass
class SourceMetadata:
    """Metadata associated with an ingested source."""

    url: str
    date: str
    hash: str
    trust: float
    expires_at: str | None = None


class SourceStore(Protocol):
    """Protocol describing store operations."""

    def ingest_source(
        self,
        url: str,
        content: str,
        trust: float,
        expires_at: datetime | None = None,
    ) -> str: ...

    def get_metadata(self, source_id: str) -> SourceMetadata | None: ...

    def cleanup(self) -> None: ...


class MemorySourceStore:
    """In-memory store with optional TTL and trust filtering."""

    def __init__(self, ttl: int | None = None, min_trust: float = 0.0):
        self._db: dict[str, SourceMetadata] = {}
        self.ttl = ttl
        self.min_trust = min_trust

    def close(self) -> None:  # pragma: no cover - nothing to release
        """Interface compatibility method."""
        return None

    def ingest_source(
        self,
        url: str,
        content: str,
        trust: float,
        expires_at: datetime | None = None,
    ) -> str:
        source_id = uuid4().hex
        if trust < self.min_trust:
            return source_id
        now = datetime.now(UTC)
        if expires_at is not None:
            exp_dt = expires_at
        elif self.ttl is not None:
            exp_dt = now + timedelta(seconds=self.ttl)
        else:
            exp_dt = None
        metadata = SourceMetadata(
            url=url,
            date=now.isoformat(),
            hash=sha256(content.encode("utf-8")).hexdigest(),
            trust=trust,
            expires_at=exp_dt.isoformat() if exp_dt else None,
        )
        self._db[source_id] = metadata
        return source_id

    def get_metadata(self, source_id: str) -> SourceMetadata | None:
        metadata = self._db.get(source_id)
        if not metadata:
            return None
        if metadata.expires_at and datetime.now(UTC) >= datetime.fromisoformat(metadata.expires_at):
            del self._db[source_id]
            return None
        if metadata.trust < self.min_trust:
            del self._db[source_id]
            return None
        return metadata

    def cleanup(self) -> None:
        now = datetime.now(UTC)
        expired = [
            k
            for k, v in self._db.items()
            if (v.expires_at and datetime.fromisoformat(v.expires_at) <= now)
            or v.trust < self.min_trust
        ]
        for key in expired:
            del self._db[key]


class RedisSourceStore:
    """Redis-backed store relying on Redis for TTL and trust management."""

    def __init__(
        self, redis_client: redis.Redis[Any], ttl: int | None = None, min_trust: float = 0.0
    ) -> None:
        self.redis = redis_client
        self.ttl = ttl
        self.min_trust = min_trust

    def close(self) -> None:
        """Close the underlying Redis client if supported."""

        close = getattr(self.redis, "close", None)
        if callable(close):  # pragma: no branch - simple guard
            close()

    def ingest_source(
        self,
        url: str,
        content: str,
        trust: float,
        expires_at: datetime | None = None,
    ) -> str:
        source_id = uuid4().hex
        if trust < self.min_trust:
            return source_id
        now = datetime.now(UTC)
        if expires_at is not None:
            exp_dt = expires_at
        elif self.ttl is not None:
            exp_dt = now + timedelta(seconds=self.ttl)
        else:
            exp_dt = None
        metadata = SourceMetadata(
            url=url,
            date=now.isoformat(),
            hash=sha256(content.encode("utf-8")).hexdigest(),
            trust=trust,
            expires_at=exp_dt.isoformat() if exp_dt else None,
        )
        mapping = {k: str(v) for k, v in metadata.__dict__.items() if v is not None}
        redis_mapping = cast(
            Mapping[str | bytes, bytes | float | int | str],
            mapping,
        )
        self.redis.hset(source_id, mapping=redis_mapping)
        if exp_dt:
            ttl_seconds = int((exp_dt - now).total_seconds())
            if ttl_seconds > 0:
                self.redis.expire(source_id, ttl_seconds)
            else:
                self.redis.delete(source_id)
        return source_id

    def get_metadata(self, source_id: str) -> SourceMetadata | None:
        data = self.redis.hgetall(source_id)
        if not data:
            return None
        metadata = SourceMetadata(
            url=data[b"url"].decode(),
            date=data[b"date"].decode(),
            hash=data[b"hash"].decode(),
            trust=float(data[b"trust"].decode()),
            expires_at=data[b"expires_at"].decode() if b"expires_at" in data else None,
        )
        if metadata.expires_at and datetime.now(UTC) >= datetime.fromisoformat(metadata.expires_at):
            self.redis.delete(source_id)
            return None
        if metadata.trust < self.min_trust:
            self.redis.delete(source_id)
            return None
        return metadata

    def cleanup(self) -> None:  # pragma: no cover - Redis handles TTL itself
        return


def _build_store() -> SourceStore:
    settings = load_settings()
    if settings.source_store_backend == "redis":
        client = redis.from_url(settings.source_store_redis_url or "redis://localhost")
        return RedisSourceStore(client, ttl=settings.source_store_ttl_seconds)
    return MemorySourceStore(ttl=settings.source_store_ttl_seconds)


_FACTORY: StoreFactory[SourceStore] = StoreFactory("source", _build_store)


def get_store() -> SourceStore:
    """Return the active source store backend."""

    return _FACTORY.get()


def connect_store() -> SourceStore:
    """Ensure the source store backend is initialized."""

    return _FACTORY.connect()


def reconnect_store() -> SourceStore:
    """Rebuild the store backend, closing any existing connections."""

    return _FACTORY.reconnect()


def close_store() -> None:
    """Close the active store backend and release resources."""

    _FACTORY.close()


def ingest_source(
    url: str,
    content: str,
    trust: float,
    expires_at: datetime | None = None,
) -> str:
    """Generate a unique ``source_id`` and persist metadata."""

    store = get_store()
    return store.ingest_source(url, content, trust, expires_at)


def get_metadata(source_id: str) -> SourceMetadata | None:
    """Return stored metadata for ``source_id`` if present."""

    store = get_store()
    return store.get_metadata(source_id)


def cleanup_expired_entries() -> None:
    """Remove expired entries for in-memory backend."""

    store = get_store()
    store.cleanup()


__all__ = [
    "close_store",
    "connect_store",
    "get_store",
    "MemorySourceStore",
    "RedisSourceStore",
    "SourceMetadata",
    "cleanup_expired_entries",
    "get_metadata",
    "ingest_source",
]
