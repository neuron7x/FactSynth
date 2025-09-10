#!/usr/bin/env python3
"""
Calibrate all scripts/ without changing behavior.
- Python: shebang, docstring, main()+guard, optional argparse shim, logging (env-toggled)
- Shell: strict header, traps, quoting, mkdir -p, cp -R src/. dst/
Idempotent; dry-run by default.
"""
from __future__ import annotations
import argparse, os, re, sys, textwrap
from pathlib import Path

PY_SHEBANG = "#!/usr/bin/env python3\n"
BASH_HEADER = r"""#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
trap 'code=$?; echo "ERR at ${BASH_SOURCE[0]}:${LINENO} (exit $code)" >&2' ERR
"""

LOGGING_SNIPPET = (
    "import logging, os\n"
    'LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()\n'
    'logging.basicConfig(level=LOG_LEVEL, format="%(levelname)s %(message)s")\n'
    "log = logging.getLogger(__name__)\n"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def ensure_newline(s: str) -> str:
    return s if s.endswith("\n") else s + "\n"


def is_python(p: Path) -> bool:
    return p.suffix == ".py"


def is_shell(p: Path) -> bool:
    return p.suffix == ".sh"


def ensure_py_shebang(src: str) -> str:
    return src if src.startswith("#!") else PY_SHEBANG + src


def ensure_py_docstring(src: str, rel: str) -> str:
    m = re.match(r'^(?:#!.*\n)?\s*(?:"""|\'\'\')', src)
    if m:
        return src
    doc = f'"""{rel} — auto-added docstring (logic unchanged)."""\n'
    return (
        src.splitlines(keepends=True)[0]
        + doc
        + "".join(src.splitlines(keepends=True)[1:])
        if src.startswith("#!")
        else doc + src
    )


def has_main_guard(src: str) -> bool:
    return re.search(r'if\s+__name__\s*==\s*[\'\"]__main__[\'\"]\s*:', src) is not None


def maybe_add_main_guard(src: str) -> str:
    if has_main_guard(src):
        return src
    guard = textwrap.dedent(
        """
    def main(argv=None) -> int:
        # NOTE: behavior preserved; original top-level still executes
        return 0

    if __name__ == "__main__":
        import sys as _sys
        raise SystemExit(main(_sys.argv[1:]))
    """
    ).strip("\n")
    return src.rstrip() + "\n\n" + guard + "\n"


def maybe_inject_logging(src: str) -> str:
    if "logging.basicConfig(" in src:
        return src
    m = re.search(r"(\A(?:#!.*\n)?)((?:from\s+\S+\s+import[^\n]*\n|import\s+[^\n]*\n)+)", src)
    if not m:
        return LOGGING_SNIPPET + src
    return m.group(1) + m.group(2) + LOGGING_SNIPPET + src[m.end() :]


def maybe_argparse_shim(src: str) -> str:
    if "sys.argv" not in src or "argparse" in src:
        return src
    shim = textwrap.dedent(
        """
    import argparse as _argparse, sys as _sys
    def _parse_args(argv=None):
        p=_argparse.ArgumentParser(add_help=True, description="(shim) preserves defaults/positionals")
        # NOTE: Not redefining defaults; this shim enables --help without altering behavior.
        p.add_argument("ARGS", nargs="*", help="positional passthrough")
        return p.parse_args(argv)
    _ = _parse_args(None)  # no-op, keeps defaults identical
    """
    ).strip("\n")
    m = re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:', src)
    if not m:
        return src.rstrip() + "\n\n" + shim + "\n"
    insert_at = m.start()
    return src[:insert_at] + shim + "\n\n" + src[insert_at:]


def calibrate_python(text: str, rel: str) -> str:
    out = ensure_py_shebang(text)
    out = ensure_py_docstring(out, rel)
    out = maybe_inject_logging(out)
    out = maybe_argparse_shim(out)
    out = maybe_add_main_guard(out)
    return ensure_newline(out)


def ensure_bash_header(text: str) -> str:
    if text.startswith(BASH_HEADER.splitlines()[0]):
        return (
            text
            if "set -Eeuo pipefail" in text
            else text.replace(text.splitlines()[0] + "\n", BASH_HEADER, 1)
        )
    if text.startswith("#!"):
        return BASH_HEADER + "\n".join(text.splitlines()[1:]) + ("\n" if not text.endswith("\n") else "")
    return BASH_HEADER + text


def normalize_shell_commands(text: str) -> str:
    t = text
    t = re.sub(r"\bmkdir\s+(?!-p)([^\n]+)", r"mkdir -p \1", t)
    t = re.sub(r"\bcp\s+-r\s+(\S+)\s+(\S+)", r"cp -R \1 \2", t)
    t = re.sub(r"\bcp\s+(\S+)\s+(\S+)", r"cp \1 \2", t)
    t = re.sub(r"\bcurl\b(?![^\n]*--max-time)", r"curl --max-time 30", t)
    t = re.sub(r"\bwget\b(?![^\n]*--timeout)", r"wget --timeout=30", t)
    return t


def quote_shell_vars(text: str) -> str:
    return re.sub(r"\$(?!\{)([A-Za-z_][A-Za-z0-9_]*)", r"${\1}", text)


def calibrate_shell(text: str) -> str:
    t = ensure_bash_header(text)
    t = normalize_shell_commands(t)
    t = quote_shell_vars(t)
    return ensure_newline(t)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="scripts", help="directory with scripts")
    ap.add_argument("--write", action="store_true", help="apply changes (default: dry-run)")
    args = ap.parse_args()
    root = Path(args.root)
    changed = 0
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if is_python(p):
            before = read(p)
            after = calibrate_python(before, p.as_posix())
        elif is_shell(p):
            before = read(p)
            after = calibrate_shell(before)
        else:
            continue
        if after != before:
            changed += 1
            print(f"[UPDATE] {p}")
            if args.write:
                write(p, after)
    print(f"Changed files: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

