#!/usr/bin/env python3
import json
import pathlib
import sys

import yaml  # type: ignore

API_GUARD = "Do not change FactSynth runtime API"


def main() -> None:
    root = pathlib.Path(".")
    prompt = root / "prompts" / "factsynth_lock.system.md"
    examples = root / "tests" / "factsynth_lock_examples.json"
    doc = root / "docs" / "FACTSYNTH_LOCK.md"
    policy = root / "config" / "quality_policy.yaml"
    ok = True

    for path in (prompt, doc, policy):
        if not path.exists():
            print(f"[FAIL] Missing {path}", file=sys.stderr)
            ok = False
        else:
            txt = path.read_text(encoding="utf-8", errors="ignore")
            if API_GUARD.lower() not in txt.lower():
                print(f"[FAIL] API guard missing in {path}", file=sys.stderr)
                ok = False

    if policy.exists():
        try:
            policy_data = yaml.safe_load(policy.read_text())
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] Invalid YAML in {policy}: {e}", file=sys.stderr)
            ok = False
        else:
            required = {
                "hard_filters",
                "weights",
                "evidence_strength",
                "diversity",
                "recency",
                "thresholds",
            }
            if not isinstance(policy_data, dict):
                print(f"[FAIL] {policy} must be a mapping", file=sys.stderr)
                ok = False
            else:
                missing = required - policy_data.keys()
                if missing:
                    print(
                        f"[FAIL] {policy} missing keys: {sorted(missing)}",
                        file=sys.stderr,
                    )
                    ok = False

    if not examples.exists():
        print(f"[FAIL] Missing {examples}", file=sys.stderr)
        ok = False
    else:
        try:
            data = json.loads(examples.read_text())
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] Invalid JSON in {examples}: {e}", file=sys.stderr)
            ok = False
        else:
            if not isinstance(data, list):
                print(f"[FAIL] {examples} must be a list", file=sys.stderr)
                ok = False
            for case in data if isinstance(data, list) else []:
                if not isinstance(case, dict) or not {"name", "request", "expected"} <= case.keys():
                    print(f"[FAIL] Invalid case entry: {case}", file=sys.stderr)
                    ok = False
                    continue
                fixture = root / "tests" / case["request"]
                if not fixture.exists():
                    print(f"[FAIL] Missing fixture {fixture}", file=sys.stderr)
                    ok = False
                expected = case.get("expected")
                metrics = {"rmse", "fcr", "pfi"}
                if not isinstance(expected, dict) or metrics - expected.keys():
                    print(
                        f"[FAIL] Case {case['name']} expected metrics {sorted(metrics)}",
                        file=sys.stderr,
                    )
                    ok = False
                elif not all(isinstance(v, (int, float)) for v in expected.values()):
                    print(f"[FAIL] Non-numeric expected values in {case['name']}", file=sys.stderr)
                    ok = False
    if not ok:
        sys.exit(1)
    print(json.dumps({"status": "ok"}))


if __name__ == "__main__":
    main()
