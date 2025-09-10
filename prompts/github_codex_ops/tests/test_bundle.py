import json
from pathlib import Path

BUNDLE_SIZE = 12


def test_golden_12():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "GOLDEN_12_TESTSET.json").read_text())
    assert isinstance(data, list) and len(data) == BUNDLE_SIZE
    for item in data:
        assert "id" in item and "description" in item
