#!/usr/bin/env bash
set -euo pipefail
rm -rf dist build *.egg-info release
python -m pip install --upgrade pip build
python -m build
mkdir -p release
cp -r dist release/
(sha256sum release/dist/* || shasum -a 256 release/dist/*) > release/CHECKSUMS.txt
echo "Release ready in ./release"
