import json
from collections import defaultdict
from pathlib import Path

import pytest


@pytest.mark.fairness
def test_demographic_parity_within_threshold():
    data_file = Path(__file__).parent / "data" / "fairness_control.json"
    with open(data_file, encoding="utf-8") as f:
        records = json.load(f)

    counts = defaultdict(int)
    positives = defaultdict(int)
    for record in records:
        group = record["group"]
        pred = record["prediction"]
        counts[group] += 1
        positives[group] += int(pred)

    rates = {g: positives[g] / counts[g] for g in counts}
    max_rate = max(rates.values())
    min_rate = min(rates.values())
    disparity = max_rate - min_rate

    THRESHOLD = 0.1
    assert disparity < THRESHOLD, (
        f"Demographic parity disparity {disparity:.2f} exceeds threshold"
    )
