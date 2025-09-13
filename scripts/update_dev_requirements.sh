#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
import pathlib
try:
    import tomllib
except ModuleNotFoundError:  # Python <3.11
    import tomli as tomllib

data = tomllib.loads(pathlib.Path('pyproject.toml').read_text())
dev_deps = data.get('project', {}).get('optional-dependencies', {}).get('dev', [])
pathlib.Path('requirements-dev.txt').write_text("\n".join(dev_deps) + ("\n" if dev_deps else ""))
PY
