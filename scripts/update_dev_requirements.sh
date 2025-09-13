#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
trap 'echo "ERR at ${BASH_SOURCE[0]}:${LINENO} (exit $?)" >&2' ERR

# Regenerate requirements-dev.txt from pyproject.toml
pip-compile pyproject.toml --extra dev --output-file requirements-dev.txt "$@"
