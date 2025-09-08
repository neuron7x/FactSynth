"""factsynth_ultimate package initialization."""
from importlib import metadata

try:
    VERSION = metadata.version("factsynth-ultimate-pro")
except metadata.PackageNotFoundError:  # pragma: no cover - fallback for dev
    VERSION = "0.0.0"

__all__ = ["VERSION"]
