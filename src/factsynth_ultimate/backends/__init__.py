from __future__ import annotations

from typing import Dict, Type

from .base import ScoreBackend
from .heuristic import HeuristicBackend
from .llm import LLMBackend
from .semantic import SemanticBackend

_REGISTRY: Dict[str, Type[ScoreBackend]] = {"heuristic": HeuristicBackend}


def register_backend(name: str, backend_cls: Type[ScoreBackend]) -> None:
    """Register a scoring backend under ``name``."""
    _REGISTRY[name] = backend_cls


def get_backend(name: str | None = None) -> ScoreBackend:
    """Return an instance of the requested backend.

    If ``name`` is ``None``, the default ``heuristic`` backend is used.
    """
    key = name or "heuristic"
    try:
        cls = _REGISTRY[key]
    except KeyError as e:  # pragma: no cover - defensive
        raise KeyError(f"Unknown scoring backend: {key}") from e
    return cls()


__all__ = [
    "ScoreBackend",
    "HeuristicBackend",
    "LLMBackend",
    "SemanticBackend",
    "register_backend",
    "get_backend",
]
