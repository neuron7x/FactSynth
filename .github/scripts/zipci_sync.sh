#!/usr/bin/env bash
set -euo pipefail
STAGING="${1:?staging_dir_required}"
PROTECTED=( ".github/**" ".git/**" ".gitignore" "CODEOWNERS" "SECURITY.md" )
EXCLUDES=()
if [ -f .zipci-ignore ]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    EXCLUDES+=( "--exclude=$line" )
  done < .zipci-ignore
fi
for p in "${PROTECTED[@]}"; do EXCLUDES+=( "--exclude=$p" ); done
rsync -a --delete "${EXCLUDES[@]}" "$STAGING/" "./"
