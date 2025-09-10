#!/usr/bin/env python3
import sys, json, pathlib, re
API_GUARD = "Do not change FactSynth runtime API"
ROOT = pathlib.Path('.')

def fail(msg): print(f"[FAIL] {msg}", file=sys.stderr); sys.exit(1)
def ok(): print('{"status":"ok"}')

def ensure_guard(p: pathlib.Path):
    if API_GUARD.lower() not in p.read_text(encoding='utf-8').lower():
        fail(f"API guardrail missing in {p}")

def validate_examples(p: pathlib.Path):
    data = json.loads(p.read_text(encoding='utf-8'))
    for i,case in enumerate(data):
        if "claim" not in case or "expect_status" not in case:
            fail(f"{p}[{i}] invalid shape")

def main():
    docs = ROOT/'docs/FACTSYNTH_LOCK.md'
    prompt = ROOT/'prompts/factsynth_lock.system.md'
    examples = ROOT/'tests/factsynth_lock_examples.json'
    for p in [docs,prompt]:
        if not p.exists(): fail(f"Missing {p}")
        ensure_guard(p)
        if len(p.read_text(encoding='utf-8')) > 30000:
            fail(f"{p} too long")
    if not examples.exists(): fail(f"Missing {examples}")
    validate_examples(examples)
    ok()

if __name__=='__main__':
    main()
