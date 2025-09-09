import json
from pathlib import Path

def test_golden_12():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "GOLDEN_12_TESTSET.json").read_text())
    assert isinstance(data, list) and len(data) == 12
    for item in data:
        assert isinstance(item, dict)
        for field in ("id", "context", "question", "expected"):
            assert field in item
