#!/usr/bin/env bash
set -euo pipefail

JSON_FILE="${1:?json file}"
SCHEMA_FILE="${2:?schema file}"

# Requires Node.js with ajv-cli installed: npm i -g ajv-cli
if ! command -v ajv >/dev/null; then
  echo "Please install ajv-cli: npm i -g ajv-cli" >&2
  exit 2
fi

ajv validate -s "${SCHEMA_FILE}" -d "${JSON_FILE}" --spec=draft2020
echo "VALID: ${JSON_FILE} ✨"
