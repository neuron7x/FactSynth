import json
from pathlib import Path

EXPECTED_ITEMS = 12

def test_golden_12():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "GOLDEN_12_TESTSET.json").read_text())
    assert isinstance(data, list) and len(data) == EXPECTED_ITEMS
    for item in data:
        assert isinstance(item, dict)
        for field in ("id", "context", "question", "expected"):
            assert field in item
