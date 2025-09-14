import itertools
import json
from pathlib import Path

import pytest
import yaml

LOCALES_DIR = Path(__file__).resolve().parents[1] / "src" / "factsynth_ultimate" / "locales"


def _load_keys(path: Path) -> set[str]:
    if path.suffix == ".json":
        data = json.loads(path.read_text())
    elif path.suffix in {".yml", ".yaml"}:
        data = yaml.safe_load(path.read_text())
    else:
        raise ValueError(f"Unsupported locale file: {path.suffix}")
    return set(data.keys())


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_i18n_catalog_parity() -> None:
    catalogs = {p.stem: _load_keys(p) for p in LOCALES_DIR.iterdir() if p.is_file()}
    for (lang_a, keys_a), (lang_b, keys_b) in itertools.combinations(catalogs.items(), 2):
        extra_a = keys_a - keys_b
        extra_b = keys_b - keys_a
        assert not extra_a and not extra_b, (
            f"{lang_a} vs {lang_b} mismatch: "
            f"{lang_a} only {sorted(extra_a)}, {lang_b} only {sorted(extra_b)}"
        )
