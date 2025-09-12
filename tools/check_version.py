#!/usr/bin/env python3
"""Check version consistency across project files."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml
import tomllib

ROOT = Path(__file__).resolve().parents[1]

py_ver = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
openapi_ver = yaml.safe_load((ROOT / "openapi" / "openapi.yaml").read_text())["info"]["version"]

spec = importlib.util.spec_from_file_location(
    "pkg", ROOT / "src" / "factsynth_ultimate" / "__init__.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load project spec")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
code_ver = module.VERSION

if len({py_ver, openapi_ver, code_ver}) != 1:
    print(
        f"Version mismatch: pyproject={py_ver}, openapi={openapi_ver}, code={code_ver}",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"Version {py_ver} consistent across files")
