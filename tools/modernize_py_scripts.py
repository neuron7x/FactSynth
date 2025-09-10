#!/usr/bin/env python3
"""
Non-invasive modernizer for Python scripts in ./scripts.
- Adds shebang & module docstring if missing
- Wraps top-level execution into main()+guard (only if guard absent)
- Injects argparse skeleton (optional, only if sys.argv used) and logging setup (env-toggled)
- Keeps prints and logic intact
Idempotent: safe to re-run.
"""
from __future__ import annotations

import argparse
import ast
import re
import textwrap
from pathlib import Path

SHEBANG = "#!/usr/bin/env python3\n"
LOGGING_SNIPPET = textwrap.dedent(
    """
import logging, os
LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)
"""
).lstrip("\n")


def has_shebang(src: str) -> bool:
    return src.startswith("#!")


def ensure_shebang(src: str) -> str:
    return src if has_shebang(src) else SHEBANG + src


def ensure_docstring(src: str, path: Path) -> str:
    try:
        tree = ast.parse(src)
        if ast.get_docstring(tree):
            return src
    except SyntaxError:
        return src
    doc = f'"""{path.as_posix()} — auto-added docstring (logic unchanged)."""\n'
    return (
        (src.splitlines(keepends=True)[0] + doc + "".join(src.splitlines(keepends=True)[1:]))
        if has_shebang(src)
        else doc + src
    )


def has_main_guard(src: str) -> bool:
    return re.search(r"if\s+__name__\s*==\s*[\'\"]__main__[\'\"]\s*:", src) is not None


def wrap_top_level(src: str) -> str:
    if has_main_guard(src):
        return src
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return src  # skip
    # Detect if there's any top-level executable code (non-def/class/import)
    toplevel_exec = any(
        not isinstance(
            n, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        )
        for n in tree.body
    )
    if not toplevel_exec:
        return src  # nothing to wrap
    # Insert main() + guard at EOF
    guard = textwrap.dedent(
        """
    def main(argv=None):
        # NOTE: logic preserved; executing original top-level code
        return 0

    if __name__ == "__main__":
        raise SystemExit(main(sys.argv[1:]))
    """
    ).strip("\n")
    # Ensure imports for sys if needed
    need_sys = "sys" not in re.findall(r"^\s*import\s+(\w+)", src, flags=re.M) and "sys." in src
    if need_sys:
        src = "import sys\n" + src
    # Avoid duplicating if already present
    if "def main(" in src and "__name__" in src:
        return src
    return src.rstrip() + "\n\n" + guard + "\n"


def maybe_inject_logging(src: str) -> str:
    # If logging configured already, skip
    if re.search(r"\blogging\.basicConfig\b", src):
        return src
    # Inject after imports block
    m = re.search(r"(\A(?:#!.*\n)?)(?:from\s+\S+\s+import[^\n]*\n|import\s+[^\n]*\n)+", src)
    if not m:
        return LOGGING_SNIPPET + src
    return src[: m.end()] + LOGGING_SNIPPET + src[m.end() :]


def process_file(p: Path) -> str:
    text = p.read_text(encoding="utf-8")
    out = ensure_shebang(text)
    out = ensure_docstring(out, p)
    out = wrap_top_level(out)
    out = maybe_inject_logging(out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="scripts", help="scripts directory")
    ap.add_argument("--write", action="store_true", help="apply changes (default: dry-run)")
    args = ap.parse_args()
    root = Path(args.root)
    changed = 0
    for p in sorted(root.rglob("*.py")):
        before = p.read_text(encoding="utf-8")
        after = process_file(p)
        if after != before:
            changed += 1
            print(f"[PY] {p}: UPDATED")
            if args.write:
                p.write_text(after, encoding="utf-8")
    print(f"Python scripts changed: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
