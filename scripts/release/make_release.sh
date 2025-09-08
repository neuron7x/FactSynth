#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || echo "$(pwd)")"
cd "$repo_root"

PYVER=$(python - <<'PY'
import sys
try:
    import tomllib
    data = tomllib.loads(open('pyproject.toml','rb').read())
    print(data['project']['version'])
except Exception:
    import os
    print(os.environ.get('VERSION_FALLBACK','0.0.0'))
PY
)

VERSION="${PYVER}"
STAMP="$(date -u +%Y%m%d)"
OUTDIR="release"
PKGDIR="${OUTDIR}/factsynth-${VERSION}"
mkdir -p "$PKGDIR"

# Collect canonical contents
cp -a README.md README_UA.md LICENSE "$PKGDIR" 2>/dev/null || true
cp -a openapi "$PKGDIR"/openapi 2>/dev/null || true
cp -a grafana "$PKGDIR"/grafana 2>/dev/null || true
cp -a k8s "$PKGDIR"/k8s 2>/dev/null || true
cp -a charts "$PKGDIR"/charts 2>/dev/null || true
cp -a examples "$PKGDIR"/examples 2>/dev/null || true
cp -a dist "$PKGDIR"/dist 2>/dev/null || true
cp -a docs "$PKGDIR"/docs 2>/dev/null || true

# Include minimal quickstart
mkdir -p "$PKGDIR/quickstart"
cat > "$PKGDIR/quickstart/run.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv && . .venv/bin/activate
pip install -U pip
pip install -e .[ops]
export API_KEY=change-me
uvicorn factsynth_ultimate.app:app --host 0.0.0.0 --port 8000
SH
chmod +x "$PKGDIR/quickstart/run.sh"

# SBOM if syft is present
if command -v syft >/dev/null 2>&1; then
  syft packages . -o spdx-json > "${PKGDIR}/SBOM.spdx.json" || true
fi

# Checksums
pushd "$OUTDIR" >/dev/null
ZIP="factsynth-${VERSION}-release-${STAMP}.zip"
rm -f "$ZIP"
zip -r "$ZIP" "factsynth-${VERSION}" >/dev/null
sha256sum "$ZIP" > SHA256SUMS
popd >/dev/null

echo "::notice title=Release Packaged::${OUTDIR}/${ZIP} created"
