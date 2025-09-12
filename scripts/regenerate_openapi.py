#!/usr/bin/env python3
"""Regenerate OpenAPI spec using FastAPI app."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

root = Path(__file__).resolve().parents[1]
sys.path.append(str(root / "src"))
from factsynth_ultimate.app import app  # type: ignore  # noqa: E402
from factsynth_ultimate import VERSION  # noqa: E402


def main() -> None:
    spec = app.openapi()
    spec["info"]["version"] = VERSION
    out = root / "openapi" / "openapi.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(spec, sort_keys=False))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
