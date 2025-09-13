"""Simple trace object used to propagate ``source_id`` through the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..tokenization import normalize
from .source_store import ingest_source


@dataclass
class Trace:
    """Trace information retained across processing stages."""

    source_id: str
    url: str
    content: str


def start_trace(
    url: str,
    content: str,
    trust: float = 1.0,
    expires_at: datetime | None = None,
) -> Trace:
    """Ingest *content* and return a new :class:`Trace` with ``source_id``."""

    source_id = ingest_source(url, content, trust, expires_at)
    return Trace(source_id=source_id, url=url, content=content)


def parse(trace: Trace) -> Trace:
    """Parsing stage placeholder keeping ``source_id`` intact."""

    return trace


def normalize_trace(trace: Trace) -> Trace:
    """Normalize the trace content while preserving ``source_id``."""

    trace.content = normalize(trace.content)
    return trace


def index(trace: Trace) -> Trace:
    """Indexing stage placeholder preserving ``source_id``."""

    return trace


__all__ = ["Trace", "index", "normalize_trace", "parse", "start_trace"]
