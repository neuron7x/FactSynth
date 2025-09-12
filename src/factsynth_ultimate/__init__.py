"""factsynth_ultimate package initialization."""

from importlib import metadata

try:
    VERSION = metadata.version("factsynth-ultimate-pro")
except metadata.PackageNotFoundError:  # pragma: no cover - fallback for dev
    try:  # load version from pyproject for editable installs
        import pathlib
        import tomllib

        _root = pathlib.Path(__file__).resolve().parents[2]
        VERSION = tomllib.loads((_root / "pyproject.toml").read_text())["project"]["version"]
    except Exception:  # noqa: BLE001 - best effort
        VERSION = "0.0.0"

__all__ = ["VERSION"]
