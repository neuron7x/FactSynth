#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${FACTSYNTH_API_KEY:-}"
HDR_AUTH=("x-api-key: ${API_KEY}")

echo "== FactSynth quickstart =="
if [[ -z "${API_KEY}" ]]; then
  echo "Set FACTSYNTH_API_KEY env var before running." >&2
  exit 1
fi

echo "-- healthz"
curl -fsS "${API_URL}/v1/healthz" >/dev/null && echo "OK /healthz"

echo "-- version"
curl -fsS "${API_URL}/v1/version" | tee /tmp/version.json

echo "-- generate example"
curl -fsS -H "${HDR_AUTH[@]}" -H 'content-type: application/json' \
  -d '{"text":"Sample text about SDK v3 and OIDC.","max_len":120,"max_sentences":2,"include_score":true}' \
  "${API_URL}/v1/generate" | tee /tmp/generate.json

echo "-- score example"
curl -fsS -H "${HDR_AUTH[@]}" -H 'content-type: application/json' \
  -d '{"text":"Our 2026 roadmap covers SDK v3, Redis cache, OIDC.","targets":["SDK v3","OIDC","Helm chart","Prometheus metrics"]}' \
  "${API_URL}/v1/score" | tee /tmp/score.json

echo "-- validate schemas"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"${DIR}/scripts/validate.sh" /tmp/generate.json "${DIR}/SCHEMAS/generate.output.schema.json"
"${DIR}/scripts/validate.sh" /tmp/score.json "${DIR}/SCHEMAS/score.output.schema.json"

echo "-- compute checksums"
"${DIR}/scripts/checksums.sh" "${DIR}"

echo "Done."
