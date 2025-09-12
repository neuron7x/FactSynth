#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
code=0
trap 'code=$?; echo "ERR at ${BASH_SOURCE[0]}:${LINENO} (exit ${code})" >&2' ERR

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "${REPO_ROOT}/src/full_product" "${REPO_ROOT}/tests/full_product" "${REPO_ROOT}/.github/workflows"

cat <<'PYEOF' >"${REPO_ROOT}/src/full_product/__init__.py"
"""Full product package."""
PYEOF

cat <<'PYEOF' >"${REPO_ROOT}/tests/full_product/test_smoke.py"
def test_smoke():
    assert True
PYEOF

cat <<'YAMLEOF' >"${REPO_ROOT}/.github/workflows/ci.yml"
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .[dev,ops]
      - run: pytest
YAMLEOF

echo "Full product scaffold created."
