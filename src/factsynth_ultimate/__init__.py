"""factsynth_ultimate package initialization."""
from importlib import metadata

try:
    VERSION = metadata.version("factsynth-ultimate-pro")
except metadata.PackageNotFoundError:  # pragma: no cover - fallback for dev
    try:
        from pathlib import Path

        from setuptools_scm import get_version

        VERSION = get_version(root=str(Path(__file__).resolve().parents[2]))
    except Exception:  # noqa: BLE001 - best effort
        VERSION = "0.0.0"

__all__ = ["VERSION"]
