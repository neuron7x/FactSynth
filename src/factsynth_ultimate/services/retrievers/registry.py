"""Discovery helpers for retriever entry points."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from importlib import metadata
from importlib.metadata import EntryPoint
from pathlib import Path
from typing import Any, Iterator

from ...config import load_config
from .base import Retriever

RETRIEVER_ENTRY_POINT_GROUP = "factsynth.retrievers"
LEGACY_RETRIEVER_ENTRY_POINT_GROUPS: tuple[str, ...] = (
    "factsynth_ultimate.retrievers",
)


def _iter_entry_points_for_group(group: str) -> Iterable[EntryPoint]:
    """Return the entry points registered under ``group``."""

    try:
        candidates = metadata.entry_points(group=group)
    except TypeError:
        eps = metadata.entry_points()
        select = getattr(eps, "select", None)
        if callable(select):
            candidates = select(group=group)
        else:
            get_group = getattr(eps, "get", None)
            if callable(get_group):
                candidates = get_group(group, ())
            else:  # pragma: no cover - defensive guard
                candidates = ()
    if isinstance(candidates, dict):  # pragma: no cover - legacy mapping interface
        return tuple(candidates.get(group, ()))
    return tuple(candidates)


def iter_retriever_entry_points() -> Iterator[EntryPoint]:
    """Yield unique retriever entry points from known groups."""

    seen: set[str] = set()
    for group in (RETRIEVER_ENTRY_POINT_GROUP, *LEGACY_RETRIEVER_ENTRY_POINT_GROUPS):
        for ep in _iter_entry_points_for_group(group):
            if ep.name in seen:
                continue
            seen.add(ep.name)
            yield ep


def available_retriever_entry_points() -> list[EntryPoint]:
    """Return a list of discovered retriever entry points."""

    return list(iter_retriever_entry_points())


def available_retriever_names() -> list[str]:
    """Return the sorted names of available retrievers."""

    return sorted(ep.name for ep in iter_retriever_entry_points())


def get_retriever_entry_point(name: str) -> EntryPoint:
    """Return the entry point registered under ``name``."""

    normalized = name.strip()
    for ep in iter_retriever_entry_points():
        if ep.name == normalized:
            return ep
    raise LookupError(f"Retriever '{name}' not found")


def _ensure_retriever(candidate: Any, name: str) -> Retriever:
    if isinstance(candidate, Retriever):
        return candidate
    raise TypeError(
        f"Entry point '{name}' must resolve to a Retriever instance or factory",
    )


def load_retriever(name: str, options: Mapping[str, Any] | None = None) -> Retriever:
    """Load the retriever registered under ``name`` applying ``options`` if provided."""

    entry_point = get_retriever_entry_point(name)
    loaded = entry_point.load()
    params = dict(options or {})
    if isinstance(loaded, Retriever):
        if params:
            raise TypeError(
                f"Retriever '{name}' returned an instance and cannot accept options",
            )
        return loaded
    if callable(loaded):
        try:
            candidate = loaded(**params) if params else loaded()
        except TypeError as exc:
            if params:
                msg = f"Retriever '{name}' does not accept provided options"
                raise TypeError(msg) from exc
            raise
        return _ensure_retriever(candidate, name)
    raise TypeError(
        f"Entry point '{name}' must resolve to a Retriever instance or factory",
    )


def load_configured_retriever(path: Path | None = None) -> Retriever | None:
    """Return the retriever configured in the persistent settings, if any."""

    config = load_config(path)
    name = config.RETRIEVER_NAME
    if not name:
        return None
    options = config.RETRIEVER_OPTIONS or {}
    return load_retriever(name, options)


__all__ = [
    "RETRIEVER_ENTRY_POINT_GROUP",
    "LEGACY_RETRIEVER_ENTRY_POINT_GROUPS",
    "available_retriever_entry_points",
    "available_retriever_names",
    "get_retriever_entry_point",
    "iter_retriever_entry_points",
    "load_configured_retriever",
    "load_retriever",
]
