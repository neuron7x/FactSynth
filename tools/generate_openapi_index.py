#!/usr/bin/env python3
"""Generate OpenAPI versions index."""
from __future__ import annotations

import sys
from pathlib import Path


def main(root: str) -> None:
    base = Path(root)
    versions = sorted([p.name for p in base.iterdir() if p.is_dir()])
    items = "\n".join(f'<li><a href="{v}/">{v}</a></li>' for v in versions)
    html = (
        "<!doctype html><html><head><meta charset=\"utf-8\"/>"
        "<title>OpenAPI Versions</title></head><body>"
        "<h1>OpenAPI Versions</h1><ul>"
        f"{items}" "</ul></body></html>"
    )
    (base / "index.html").write_text(html)

EXPECTED_ARGS = 2


if __name__ == "__main__":
    if len(sys.argv) != EXPECTED_ARGS:
        print("Usage: generate_openapi_index.py <dir>")
        sys.exit(1)
    main(sys.argv[1])
