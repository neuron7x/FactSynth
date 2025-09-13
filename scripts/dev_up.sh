#!/usr/bin/env bash
set -euo pipefail
uvicorn factsynth_ultimate.app:app --host 0.0.0.0 --port 8000 --reload
