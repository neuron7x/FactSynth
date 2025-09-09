## Version

- **v1.0.0 — 2025-09-10** (Kyiv time)

## Usage Checklist

1. Choose triage mode (Express/Standard/Enterprise).
2. Fill **Create** template; generate `test_plan.md`.
3. Build datasets via **Convert**; produce `schema.json`, `test_{split}.jsonl`.
4. Run **Evaluate**; persist `metrics.json`, `run_log.md`.
5. Gate with `quality_gates.yml`; push artifacts.
6. If **FAIL**, run **Improve** and re-execute.
7. Publish **Reports Package** and `Community_Post.md`.

## File/Folder Convention

```
/gate/
  plans/test_plan.md
  data/schema.json
  data/test_dev.jsonl
  data/test_eval.jsonl
  runs/2025-09-10_v1/metrics.json
  runs/2025-09-10_v1/run_log.md
  reports/accuracy_report.md
  reports/safety_report.md
  reports/bias_report.md
  ci/quality_gates.yml
  .github/workflows/gate.yml
```

## CI Snippet (GitHub Actions)

```yaml
name: GATE
on: [push, pull_request]
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: pytest -m "accuracy or coherence or safety or robustness or performance" -q
      - run: python ci/check_quality_gates.py --config ci/quality_gates.yml --metrics runs/latest/metrics.json
```

## Minimal pytest Skeleton

```python
# tests/test_accuracy.py
import json, pytest
from evaluate import load

@pytest.mark.accuracy
def test_fact_qa_accuracy():
    data = [json.loads(l) for l in open("data/test_eval.jsonl")]
    bleu = load("bleu")
    scores = []
    for row in data:
        pred = row["response"]
        ref  = row["ground_truth"]
        scores.append(bleu.compute(predictions=[pred], references=[[ref]])["bleu"])
    assert sum(scores)/len(scores) >= 0.30  # example gate; set per plan
```
