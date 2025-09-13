"""In-memory source metadata store and ingestion helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4


@dataclass
class SourceMetadata:
    """Metadata associated with an ingested source."""

    url: str
    date: str
    hash: str


# Simple in-memory store for source metadata
_SOURCE_DB: dict[str, SourceMetadata] = {}


def ingest_source(url: str, content: str) -> str:
    """Generate a unique ``source_id`` and persist metadata.

    Parameters
    ----------
    url:
        Original location of the content.
    content:
        Raw content used to generate a stable hash.

    Returns
    -------
    str
        The generated ``source_id``.
    """

    source_id = uuid4().hex
    metadata = SourceMetadata(
        url=url,
        date=datetime.now(UTC).isoformat(),
        hash=sha256(content.encode("utf-8")).hexdigest(),
    )
    _SOURCE_DB[source_id] = metadata
    return source_id


def get_metadata(source_id: str) -> SourceMetadata | None:
    """Return stored metadata for ``source_id`` if present."""

    return _SOURCE_DB.get(source_id)


__all__ = ["SourceMetadata", "get_metadata", "ingest_source"]
