#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== GitHub Codex Ops quickstart =="
if command -v pytest >/dev/null; then
  python -m pytest "${DIR}/tests" -q
else
  echo "pytest not found; skipping tests" >&2
fi
"${DIR}/scripts/checksums.sh" "${DIR}"

echo "Done."
