#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
OUT="${ROOT}/SHASUMS256.txt"

# portable sha256
SHA_BIN=""
for c in shasum sha256sum; do
  if command -v "$c" >/dev/null; then SHA_BIN="$c"; break; fi
done
if [[ -z "$SHA_BIN" ]]; then
  echo "Install shasum or sha256sum to compute checksums." >&2
  exit 3
fi

cd "$ROOT"
: > "$OUT"
find . -type f \
  ! -name "SHASUMS256.txt" \
  -print0 | sort -z | while IFS= read -r -d '' f; do
  if [[ "$SHA_BIN" == "shasum" ]]; then
    shasum -a 256 "$f" >> "$OUT"
  else
    sha256sum "$f" >> "$OUT"
  fi
done
echo "Checksums written to $OUT"
