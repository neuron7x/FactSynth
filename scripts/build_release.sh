#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
trap 'code=$?; echo "ERR at ${BASH_SOURCE[0]}:${LINENO} (exit ${code})" >&2' ERR

rm -rf dist build *.egg-info release
python -m pip install --upgrade pip build
python -m build
mkdir -p release
cp -R dist release/
(sha256sum release/dist/* || shasum -a 256 release/dist/*) >release/CHECKSUMS.txt
echo "Release ready in ./release"
