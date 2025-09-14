#!/usr/bin/env bash
set -euo pipefail

# Update pinned GitHub Actions SHAs in workflow files.
# For each uses: owner/repo@<sha>, determine the major tag and
# update to the latest commit for that tag.

WORKFLOW_DIR=".github/workflows"

find "$WORKFLOW_DIR" -name '*.yml' -o -name '*.yaml' | while read -r file; do
  tmp="$file.tmp"
  cp "$file" "$tmp"
  while read -r line; do
    if [[ $line =~ uses:\ ([^@]+)@([0-9a-f]{40}) ]]; then
      action="${BASH_REMATCH[1]}"
      sha="${BASH_REMATCH[2]}"
      repo="https://github.com/$action"
      tag=$(git ls-remote "$repo" | grep "$sha" | awk '/refs\/tags\/v/{print $2}' | head -n1 || true)
      if [[ -z "$tag" ]]; then
        continue
      fi
      major=$(echo "$tag" | sed -E 's|refs/tags/(v[0-9]+).*|\1|')
      latest=$(git ls-remote "$repo" "refs/tags/$major" | awk '{print $1}')
      if [[ -n "$latest" && "$latest" != "$sha" ]]; then
        echo "$file: Updating $action from $sha to $latest ($major)"
        sed -i "s|$action@$sha|$action@$latest|" "$file"
      fi
    fi
  done < "$tmp"
  rm "$tmp"

done
