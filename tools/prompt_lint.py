#!/usr/bin/env python3
import json
import pathlib
import re
import sys

REQUIRED_AURELIUS = [
    r"Role\s*&\s*Mission",
    r"Capabilities\s*&\s*Non-goals",
    r"IF-THEN\s*Behavior\s*Rules",
    r"Style\s*&\s*Safety\s*Guardrails",
    r"KPI\s*&\s*Monitoring",
    r"SPEC_LOCK",
    r"Maturity\s*Ladder",
]
REQUIRED_CODEX = [
    r"Role\s*&\s*Mission",
    r"Output\s*Contract",
    r"Code\s*Quality\s*Rules",
    r"Performance\s*&\s*Complexity",
    r"Refusal\s*&\s*Safety",
]
REQUIRED_NEXUS = [
    r"(Role\s*&\s*Mission|Core Identity)",
    r"(Cognitive\s*Architecture|Perception Layer)",
    r"(Strategic\s*Processing|solution vectors|VELOCITY VECTOR)",
    r"(Response\s*Architecture|Executive Brief)",
    r"Tactical\s*Execution\s*Plan",
    r"(Validation\s*Framework)",
    r"(Specialized\s*Modes)",
    r"(Quality\s*Assurance|Pre-Flight)",
    r"(Activation\s*Protocols)",
    r"(NEXUS_LOCK|Output\s*Contract)",
]
FORBIDDEN = [r"\bпoчeкaти\b", r"\bwait\b", r"background (task|work)", r"promise to do later"]
API_GUARD = r"Do not change FactSynth runtime API"


def must(path: pathlib.Path, patterns):
    txt = path.read_text(encoding="utf-8", errors="ignore")
    for pat in patterns:
        if not re.search(pat, txt, re.I | re.M):
            print(f"[FAIL] Missing section '{pat}' in {path}", file=sys.stderr)
            return False
    return True


def forbid(path: pathlib.Path, patterns):
    ok = True
    txt = path.read_text(encoding="utf-8", errors="ignore")
    for pat in patterns:
        if re.search(pat, txt, re.I):
            print(f"[FAIL] Forbidden phrase '{pat}' in {path}", file=sys.stderr)
            ok = False
    return ok


def require_api_guard(path: pathlib.Path):
    txt = path.read_text(encoding="utf-8", errors="ignore")
    if API_GUARD.lower() not in txt.lower():
        print(f"[FAIL] API guardrail missing in {path}", file=sys.stderr)
        return False
    return True


def size_check(path: pathlib.Path, max_chars=30000):
    size = len(path.read_text(encoding="utf-8", errors="ignore"))
    if size > max_chars:
        print(f"[FAIL] {path} too long ({size} chars)", file=sys.stderr)
        return False
    return True


def main():
    root = pathlib.Path(".")
    aurelius = root / "prompts" / "aurelius.system.md"
    codex = root / "prompts" / "codex.system.md"
    nexus = root / "prompts" / "nexus.system.md"
    checks = [
        (aurelius, REQUIRED_AURELIUS),
        (codex, REQUIRED_CODEX),
        (nexus, REQUIRED_NEXUS),
    ]
    ok = True
    for p, pats in checks:
        if not p.exists():
            print(f"[FAIL] Missing file {p}", file=sys.stderr)
            ok = False
            continue
        ok &= must(p, pats)
        ok &= forbid(p, FORBIDDEN)
        ok &= require_api_guard(p)
        ok &= size_check(p)
    g12 = root / "tests" / "golden_12.yaml"
    if not g12.exists():
        print(f"[FAIL] Missing {g12}", file=sys.stderr)
        ok = False
    if not ok:
        sys.exit(1)
    print(json.dumps({"status": "ok"}))


if __name__ == "__main__":
    main()
