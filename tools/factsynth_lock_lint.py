#!/usr/bin/env python3
import json
import pathlib
import sys

API_GUARD = "Do not change FactSynth runtime API"


def main() -> None:
    root = pathlib.Path(".")
    prompt = root / "prompts" / "factsynth_lock.system.md"
    examples = root / "tests" / "factsynth_lock_examples.json"
    ok = True
    if not prompt.exists():
        print(f"[FAIL] Missing {prompt}", file=sys.stderr)
        ok = False
    else:
        txt = prompt.read_text(encoding="utf-8", errors="ignore")
        if API_GUARD.lower() not in txt.lower():
            print(f"[FAIL] API guard missing in {prompt}", file=sys.stderr)
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
                if not {"name", "request", "expected"} <= case.keys():
                    print(f"[FAIL] Invalid case entry: {case}", file=sys.stderr)
                    ok = False
                    continue
                fixture = root / "tests" / case["request"]
                if not fixture.exists():
                    print(f"[FAIL] Missing fixture {fixture}", file=sys.stderr)
                    ok = False
    if not ok:
        sys.exit(1)
    print(json.dumps({"status": "ok"}))


if __name__ == "__main__":
    main()
