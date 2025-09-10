#!/usr/bin/env python3
"""
Harden *.sh in ./scripts:
- Add strict mode, traps, safe IFS
- Fix common cp/mkdir pitfalls; quote expansions
- Idempotent and non-invasive (keeps original commands/order)
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

STRICT_HEADER = """#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\\n\\t'
trap 'code=$?; echo "ERR at ${BASH_SOURCE[0]}:${LINENO} (exit $code)" >&2' ERR
"""


def has_shebang(txt: str) -> bool:
    return txt.startswith("#!")


def ensure_header(txt: str) -> str:
    if txt.startswith(STRICT_HEADER.splitlines()[0]):
        # already bash shebang; ensure strict block exists
        if "set -Eeuo pipefail" in txt:
            return txt
        return txt.replace(txt.splitlines()[0] + "\n", STRICT_HEADER, 1)
    if has_shebang(txt):  # other shebang (e.g., /bin/bash)
        return (
            STRICT_HEADER
            + "\n".join(txt.splitlines()[1:])
            + ("\n" if not txt.endswith("\n") else "")
        )
    return STRICT_HEADER + txt


def normalize_cp_mkdir(txt: str) -> str:
    txt = re.sub(r"\bmkdir\s+(?!-p)([^\n]+)", r"mkdir -p \1", txt)
    txt = re.sub(r"\bcp\s+-r\s+(\S+)\s+(\S+)", r"cp -R \1 \2", txt)
    txt = re.sub(r"\bcp[ \t]+([^\n]+)[ \t]+([^\n]+)", r"cp \1 \2", txt)
    return txt


def quote_vars(txt: str) -> str:
    return re.sub(r"\$([A-Za-z_][A-Za-z0-9_]*)", r"${\1}", txt)


def process_file(p: Path) -> str:
    t = p.read_text(encoding="utf-8")
    t2 = ensure_header(t)
    t2 = normalize_cp_mkdir(t2)
    t2 = quote_vars(t2)
    return t2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="scripts")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    changed = 0
    for p in sorted(Path(a.root).rglob("*.sh")):
        before = p.read_text(encoding="utf-8")
        after = process_file(p)
        if after != before:
            changed += 1
            print(f"[SH] {p}: UPDATED")
            if a.write:
                p.write_text(after, encoding="utf-8")
    print(f"Bash scripts changed: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
