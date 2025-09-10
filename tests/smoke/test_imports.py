from pathlib import Path

import yaml


def test_guardrails_present():
    docs = Path("docs/FACTSYNTH_LOCK.md").read_text(encoding="utf-8")
    prompt = Path("prompts/factsynth_lock.system.md").read_text(encoding="utf-8")
    guard = "Do not change FactSynth runtime API"
    assert guard in docs
    assert guard in prompt

def test_policy_shape():
    y = yaml.safe_load(Path("config/quality_policy.yaml").read_text(encoding="utf-8"))
    for k in ["hard_filters","weights","evidence_strength","diversity","recency","thresholds"]:
        assert k in y
