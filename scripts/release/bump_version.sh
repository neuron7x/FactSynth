#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
trap 'code=$?; echo "ERR at ${BASH_SOURCE[0]}:${LINENO} (exit ${code})" >&2' ERR

NEW_VERSION=${1:?"Usage: bump_version.sh <new_version>"}


sed -i -e "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" pyproject.toml
python scripts/regenerate_openapi.py
# coverage badge may not exist; ignore failures
bash scripts/generate_coverage_badge.sh >/dev/null 2>&1 || true

echo "Version bumped to ${NEW_VERSION}"
