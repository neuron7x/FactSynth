#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'
trap 'code=$?; echo "ERR at ${BASH_SOURCE[0]}:${LINENO} (exit ${code})" >&2' ERR

python tools/make_badge.py --xml coverage.xml --out site/badges/coverage.svg || python - <<'PY'
import xml.etree.ElementTree as ET, pathlib
rate = float(ET.parse("coverage.xml").getroot().attrib.get("line-rate","0"))*100
svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="150" height="20"><rect width="80" height="20" fill="#555"/><rect x="80" width="70" height="20" fill="#97CA00"/><g fill="#fff" font-family="DejaVu Sans,Verdana,sans-serif" font-size="11"><text x="40" y="14" text-anchor="middle">coverage</text><text x="115" y="14" text-anchor="middle">{rate:.1f}%</text></g></svg>'
p=pathlib.Path("site/badges"); p.mkdir(parents=True, exist_ok=True); (p/"coverage.svg").write_text(svg)
PY
