#!/usr/bin/env bash
set -euo pipefail

# Repo Branch Cleanup — delete local & remote branches already merged into default
REPO="${REPO:-neuron7x/FactSynth}"
WORKDIR="${WORKDIR:-}"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
CONFIRM="${CONFIRM:-0}"
SKIP_REMOTE="${SKIP_REMOTE:-0}"
ONLY_PR_FIX="${ONLY_PR_FIX:-0}"
KEEP="${KEEP:-}"

cyan(){ printf "\033[1;36m%s\033[0m\n" "$*"; }
red(){ printf "\033[1;31m%s\033[0m\n" "$*" >&2; }
die(){ red "$1"; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1 || die "Missing $1"; }

need git
HAS_GH=0; command -v gh >/dev/null 2>&1 && HAS_GH=1

# --- enter repo (clone if needed) ---
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if git remote get-url origin >/dev/null 2>&1; then
    ORIGIN_URL="$(git remote get-url origin)"
    case "$ORIGIN_URL" in
      *"$REPO"*) cyan "Using origin: $ORIGIN_URL" ;;
      *) die "Current origin ($ORIGIN_URL) != expected ($REPO). Set REPO or run in correct repo." ;;
    esac
  else
    URL="https://github.com/$REPO.git"
    [ -n "$TOKEN" ] && URL="https://${TOKEN}@github.com/${REPO}.git"
    git remote add origin "$URL"
    cyan "Added origin: $URL"
  fi
else
  WORKDIR="${WORKDIR:-./repo-clean-$(date +%Y%m%d-%H%M%S)}"
  rm -rf "$WORKDIR"; mkdir -p "$WORKDIR"
  if [ $HAS_GH -eq 1 ]; then
    gh repo clone "$REPO" "$WORKDIR" -- --depth=100
  else
    URL="https://github.com/$REPO.git"
    [ -n "$TOKEN" ] && URL="https://${TOKEN}@github.com/${REPO}.git"
    git clone --depth=100 "$URL" "$WORKDIR"
  fi
  cd "$WORKDIR"
  cyan "Cloned $REPO to $WORKDIR"
fi

git fetch --all --prune

# --- resolve default branch ---
DEFAULT="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)"
if [ -n "$DEFAULT" ]; then
  DEFAULT="${DEFAULT#origin/}"
else
  DEFAULT="$(git remote show origin | sed -n '/HEAD branch/s/.*: //p')"
fi
[ -n "$DEFAULT" ] || die "Cannot determine default branch"
cyan "Default branch: $DEFAULT"

# --- protection rules ---
PROTECT_BASE='^(main|master|develop|dev|staging|preprod|production|prod|HEAD|origin/HEAD|gh-pages|docs)$'
PROTECT_PREFIX='^(release/|hotfix/)'
PROTECT_USER=""
if [ -n "$KEEP" ]; then
  # convert comma-separated to alternation
  PROTECT_USER="|(${KEEP//,/|})"
fi
PROTECT_REGEX="${PROTECT_BASE}${PROTECT_USER}"
ONLY_REGEX='.*'
if [ "$ONLY_PR_FIX" = "1" ]; then
  ONLY_REGEX='^pr-[0-9]+(-fix)?$'
fi

# --- list merged local branches ---
mapfile -t LOCAL_MERGED < <(git branch --merged "$DEFAULT" --format='%(refname:short)' \
  | sed 's/^\* //; s/^ *//; /^[[:space:]]*$/d' \
  | grep -E "$ONLY_REGEX" \
  | grep -Ev "$PROTECT_REGEX" \
  | grep -Ev "$PROTECT_PREFIX" \
  | grep -Ev "^${DEFAULT}$" || true)

# --- list merged remote branches ---
mapfile -t REMOTE_MERGED < <(git branch -r --merged "origin/$DEFAULT" --format='%(refname:short)' \
  | sed 's/^ *//; /^[[:space:]]*$/d' \
  | grep -E '^origin/' \
  | grep -Ev 'origin/HEAD' \
  | grep -E "$ONLY_REGEX" \
  | grep -Ev "origin/(${PROTECT_BASE#^})" \
  | grep -Ev "origin/${PROTECT_PREFIX#^}" \
  | grep -Ev "^origin/${DEFAULT}$" \
  | sed 's|^origin/||' \
  | sort -u || true)

cyan "Local merged candidates: ${#LOCAL_MERGED[@]}"
cyan "Remote merged candidates: ${#REMOTE_MERGED[@]}"

DRYRUN_MSG="(DRY-RUN)"; [ "$CONFIRM" = "1" ] && DRYRUN_MSG=""
cyan "Deletion mode $DRYRUN_MSG — set CONFIRM=1 to actually delete."

# --- delete locals ---
DEL_L=0; SKIP_L=0
for b in "${LOCAL_MERGED[@]}"; do
  if [[ "$b" =~ $PROTECT_BASE ]] || [[ "$b" =~ $PROTECT_PREFIX ]]; then
    ((SKIP_L++)); cyan "skip local: $b (protected)"; continue
  fi
  if [ "$CONFIRM" = "1" ]; then
    if git branch -d "$b"; then ((DEL_L++)); fi
  else
    cyan "would delete local: $b"
  fi
done

# --- delete remotes ---
DEL_R=0; SKIP_R=0
if [ "$SKIP_REMOTE" != "1" ]; then
  for b in "${REMOTE_MERGED[@]}"; do
    if [[ "$b" =~ $PROTECT_BASE ]] || [[ "$b" =~ $PROTECT_PREFIX ]]; then
      ((SKIP_R++)); cyan "skip remote: $b (protected)"; continue
    fi
    if [ "$CONFIRM" = "1" ]; then
      if git push origin --delete "$b"; then ((DEL_R++)); fi
    else
      cyan "would delete remote: $b"
    fi
  done
else
  cyan "Skipping remote deletion (SKIP_REMOTE=1)"
fi

cyan "Summary:"
printf "  Local deleted:  %d\n" "$DEL_L"
printf "  Local skipped:  %d\n" "$SKIP_L"
printf "  Remote deleted: %d\n" "$DEL_R"
printf "  Remote skipped: %d\n" "$SKIP_R"
[ "$CONFIRM" = "1" ] || cyan "Nothing actually deleted. Re-run with CONFIRM=1 to apply."
