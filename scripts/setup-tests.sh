#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
trap 'echo "ERR at ${BASH_SOURCE[0]}:${LINENO} (exit $?)" >&2' ERR

pip install -U pip
pip install -e '.[dev,isr,numpy]'
