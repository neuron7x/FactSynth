from __future__ import annotations

import json
from pathlib import Path

import yaml

from factsynth_ultimate import i18n


def _collect_keys(obj: dict, prefix: tuple[str, ...] = ()) -> set[str]:
    keys: set[str] = set()
    for key, value in obj.items():
        path = (*prefix, key)
        if isinstance(value, dict):
            keys |= _collect_keys(value, path)
        else:
            keys.add(".".join(path))
    return keys


def _load_catalog(path: Path) -> dict:
    if path.suffix == ".json":
        return json.loads(path.read_text())
    if path.suffix in {".yaml", ".yml"}:
        return yaml.safe_load(path.read_text())
    raise AssertionError(f"Unsupported locale file: {path}")


def test_i18n_catalog_parity(httpx_mock) -> None:
    httpx_mock.reset()
    catalogs: dict[str, set[str]] = {}
    for path in i18n.LOCALES_DIR.glob("*"):
        if path.is_file():
            catalogs[path.stem] = _collect_keys(_load_catalog(path))
    assert catalogs, "No locale catalogs found"

    all_keys = set().union(*catalogs.values())
    missing = {lang: sorted(all_keys - keys) for lang, keys in catalogs.items() if all_keys - keys}
    assert not missing, f"Missing keys: {missing}"
