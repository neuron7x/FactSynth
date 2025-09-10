#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
trap 'code=$?; echo "ERR at ${BASH_SOURCE[0]}:${LINENO} (exit ${code})" >&2' ERR
set -euo pipefail

pip install -U pip
pip install -e .[dev,isr,numpy]
