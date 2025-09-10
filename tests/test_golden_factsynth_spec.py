import json
from pathlib import Path

EXPECTED_ITEMS = 12


def test_golden_factsynth_schema():
    data = json.loads(Path("tests/golden_factsynth.json").read_text())
    assert isinstance(data, list)
    assert len(data) == EXPECTED_ITEMS
    ids = set()
    for item in data:
        assert {"id", "name", "description"} <= item.keys()
        assert isinstance(item["id"], int) and item["id"] >= 1
        assert item["name"]
        assert item["description"]
        assert item["id"] not in ids
        ids.add(item["id"])
