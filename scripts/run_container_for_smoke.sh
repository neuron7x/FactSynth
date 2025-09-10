#!/usr/bin/env bash
set -euo pipefail
IMAGE="${1:-ghcr.io/${GITHUB_REPOSITORY_OWNER}/${GITHUB_REPOSITORY#*/}:latest}"
CID=""
cleanup(){ [ -n "$CID" ] && docker rm -f "$CID" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker pull "$IMAGE" || true
CID=$(docker run -d "$IMAGE")
PORT=$(docker inspect "$CID" | jq -r '.[0].Config.ExposedPorts | keys[0] // "8000/tcp"' | cut -d/ -f1)
HOSTP=$(docker inspect "$CID" | jq -r ".[0].NetworkSettings.Ports[\"${PORT}/tcp\"][0].HostPort // empty")
[ -z "$HOSTP" ] && { docker stop "$CID"; CID=$(docker run -d -p ${PORT}:${PORT} "$IMAGE"); HOSTP="$PORT"; }
BASE="http://127.0.0.1:${HOSTP}"
echo "BASE_URL=$BASE" >> "$GITHUB_ENV"
echo "WS_URL=${BASE/https/http}"; echo "SSE_URL=$BASE/sse"
