#!/usr/bin/env bash
set -euo pipefail

# helpers
mk() { install -d "$1"; }
wr() { mkdir -p "$(dirname "$1")" && cat > "$1"; }

echo ">> creating structure"
mk src/factsynth_ultimate tests .github/workflows openapi examples/python examples/typescript tools configs k8s scripts docs

echo ">> pyproject"
wr pyproject.toml <<'EOF'
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "factsynth-ultimate"
version = "0.0.0"
description = "FactSynth — ready product (API/CLI) with tests, CI/CD, Pages."
authors = [{name = "neuron7x"}]
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
  "fastapi>=0.110",
  "uvicorn[standard]>=0.24",
  "pydantic>=2.0",
  "prometheus-client>=0.16",
  "requests>=2.31"
]
[project.optional-dependencies]
dev = ["black>=24.3","ruff>=0.6","isort>=5.13","mypy>=1.8","pre-commit>=3.6","yamllint>=1.35"]
test = ["pytest>=8.0","pytest-cov>=5.0","httpx>=0.27","openapi-spec-validator>=0.7.1","pyyaml>=6.0.1"]
[project.scripts]
factsynth = "factsynth_ultimate.cli:main"
factsynth-ultimate = "factsynth_ultimate.cli:main"
[tool.setuptools]
package-dir = {"" = "src"}
[tool.setuptools.packages.find]
where = ["src"]
include = ["factsynth_ultimate*"]
EOF

echo ">> README"
wr README.md <<'EOF'
# FactSynth Ultimate — Ready Product

API + CLI, юніт-тести з покриттям, CI/CD, GitHub Pages (coverage-бейдж, OpenAPI, live demo).

## Локальний запуск
```bash
python -m pip install -U pip
pip install -e .[test]
uvicorn factsynth_ultimate.app:app --host 0.0.0.0 --port 8000
````

## Ендпоїнти

* `GET /healthz`
* `GET /metrics`
* `POST /v1/generate` — {prompt, max_tokens} → {output}

## Бейджі (для neuron7x/FactSynth)

[![CI](https://github.com/neuron7x/FactSynth/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/neuron7x/FactSynth/actions/workflows/ci.yml)
[![CodeQL](https://github.com/neuron7x/FactSynth/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/neuron7x/FactSynth/actions/workflows/codeql.yml)
![Coverage](https://neuron7x.github.io/FactSynth/badges/coverage.svg)

__Live demo / OpenAPI (Pages):__

* Demo: [https://neuron7x.github.io/FactSynth/?api=https://your-api-host](https://neuron7x.github.io/FactSynth/?api=https://your-api-host)
* OpenAPI: [https://neuron7x.github.io/FactSynth/openapi.html](https://neuron7x.github.io/FactSynth/openapi.html)
EOF

echo ">> src"
wr src/factsynth_ultimate/__init__.py <<'EOF'
__all__ = ["__version__"]
__version__ = "0.0.0"
EOF

wr src/factsynth_ultimate/service.py <<'EOF'
from __future__ import annotations
def synthesize(prompt: str, max_tokens: int = 128) -> str:
tokens = [t for t in prompt.strip().split() if t]
trunc = tokens[: max(1, max_tokens)]
text = " ".join(trunc)
checksum = sum(ord(c) for c in text) % 997
return f"{text} |ck:{checksum:03d}"
EOF

wr src/factsynth_ultimate/app.py <<'EOF'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import CollectorRegistry, generate_latest, Counter, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from .service import synthesize

app = FastAPI(title="FactSynth API", version="")
registry = CollectorRegistry()
REQUESTS = Counter("factsynth_requests_total","Total API requests",["endpoint"],registry=registry)

class GenerateIn(BaseModel):
prompt: str = Field(..., min_length=1)
max_tokens: int = Field(128, ge=1, le=4096)

class GenerateOut(BaseModel):
output: str

@app.get("/healthz")
def healthz() -> dict: REQUESTS.labels("/healthz").inc(); return {"status":"ok"}

@app.get("/metrics")
def metrics(): return Response(content=generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

@app.post("/v1/generate", response_model=GenerateOut)
def generate(body: GenerateIn):
REQUESTS.labels("/v1/generate").inc()
try:
return {"output": synthesize(body.prompt, body.max_tokens)}
except Exception as e:
raise HTTPException(status_code=500, detail=str(e))
EOF

wr src/factsynth_ultimate/cli.py <<'EOF'
import argparse, sys, json
from .service import synthesize
from . import __version__
def main(argv=None):
avrg = argv or sys.argv[1:]
p = argparse.ArgumentParser(prog="factsynth", description="FactSynth CLI")
sub = p.add_subparsers(dest="cmd")
g = sub.add_parser("gen", help="Generate output")
g.add_argument("--prompt", required=True); g.add_argument("--max-tokens", type=int, default=128)
sub.add_parser("version", help="Show version")
a = p.parse_args(avrg)
if a.cmd == "gen":
print(json.dumps({"output": synthesize(a.prompt, a.max_tokens)}, ensure_ascii=False)); return 0
if a.cmd == "version": print(__version__); return 0
p.print_help(); return 0
if __name__ == "__main__": raise SystemExit(main())
EOF

wr src/factsynth_ultimate/__main__.py <<'EOF'
from .cli import main
if __name__ == "__main__": raise SystemExit(main())
EOF

echo ">> tests"
wr pytest.ini <<'EOF'
[pytest]
addopts = -q -ra --maxfail=1
EOF
wr .coveragerc <<'EOF'
[run]
branch = True
source = src/factsynth_ultimate
EOF
wr tests/test_app.py <<'EOF'
from fastapi.testclient import TestClient
from factsynth_ultimate.app import app
def test_healthz_ok():
c = TestClient(app); r = c.get("/healthz")
assert r.status_code == 200 and r.json().get("status") == "ok"
def test_metrics_non_empty():
c = TestClient(app); r = c.get("/metrics")
assert r.status_code == 200 and isinstance(r.text, str) and len(r.text) > 0
def test_generate_basic():
c = TestClient(app); r = c.post("/v1/generate", json={"prompt": "a b c d e", "max_tokens": 3})
assert r.status_code == 200 and r.json()["output"].startswith("a b c |ck:")
EOF
wr tests/test_service.py <<'EOF'
from factsynth_ultimate.service import synthesize
def test_synthesize_limits_and_checksum():
out = synthesize("one two three four five", max_tokens=2); assert out.startswith("one two |ck:")
out2 = synthesize(" one   two \t  ", max_tokens=5); assert out2.startswith("one two |ck:")
assert synthesize("abc", 10) == synthesize("abc", 10)
EOF
wr tests/test_cli.py <<'EOF'
import subprocess, sys, json
def test_cli_help():
p = subprocess.run([sys.executable, "-m", "factsynth_ultimate", "-h"], capture_output=True, text=True)
assert p.returncode == 0 and "FactSynth CLI" in p.stdout
def test_cli_gen():
p = subprocess.run([sys.executable, "-m", "factsynth_ultimate", "gen", "--prompt", "x y z", "--max-tokens", "2"],
capture_output=True, text=True)
assert p.returncode == 0 and json.loads(p.stdout)["output"].startswith("x y |ck:")
EOF

echo ">> openapi & examples & configs & k8s"
wr openapi/openapi.yaml <<'EOF'
openapi: 3.0.3
info: { title: FactSynth API, description: Minimal contract, version: "" }
servers: [ { url: http://localhost:8000 } ]
paths:
/healthz: { get: { summary: Liveness, responses: { '200': { description: OK } } } }
/metrics: { get: { summary: Prometheus metrics, responses: { '200': { description: OK } } } }
/v1/generate:
post:
summary: Synthesize output
requestBody:
required: true
content: { application/json: { schema: { type: object, properties:
{ prompt: { type: string, minLength: 1 }, max_tokens: { type: integer, minimum: 1, maximum: 4096, default: 128 } }, required: [prompt] } } }
responses: { '200': { description: OK, content: { application/json: { schema: { type: object, properties: { output: { type: string } } } } } } }
EOF
wr examples/python/sdk_example.py <<'EOF'
import os, requests
API = os.getenv("FACTSYNTH_API", "http://localhost:8000")
def generate(prompt: str, max_tokens: int = 128):
r = requests.post(f"{API}/v1/generate", json={"prompt": prompt, "max_tokens": max_tokens}, timeout=30)
r.raise_for_status(); return r.json()
if __name__ == "__main__": print(generate("hello world"))
EOF
wr examples/typescript/sdk_example.ts <<'EOF'
export async function generate(prompt: string, maxTokens = 128, apiBase = '') {
const r = await fetch(`${apiBase}/v1/generate`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ prompt, max_tokens: maxTokens }) });
if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json();
}
EOF
wr configs/app.sample.yaml <<'EOF'
server: { host: 0.0.0.0, port: 8000 }
logging: { level: INFO }
rate_limit: { rps: 10 }
EOF
wr k8s/deployment.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata: { name: factsynth }
spec:
replicas: 2
selector: { matchLabels: { app: factsynth } }
template:
metadata: { labels: { app: factsynth } }
spec:
containers:
- name: api
image: ghcr.io/neuron7x/factsynth:latest
ports: [ { containerPort: 8000 } ]
readinessProbe: { httpGet: { path: /healthz, port: 8000 }, initialDelaySeconds: 5, periodSeconds: 10 }
livenessProbe:  { httpGet: { path: /healthz, port: 8000 }, initialDelaySeconds: 5, periodSeconds: 10 }
------------------------------------------------------------------------------------------------------

apiVersion: v1
kind: Service
metadata: { name: factsynth }
spec:
selector: { app: factsynth }
ports: [ { port: 80, targetPort: 8000, protocol: TCP } ]
EOF
wr Dockerfile <<'EOF'
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src /app/src
RUN pip install --upgrade pip && pip install -e .[test]
EXPOSE 8000
CMD ["uvicorn","factsynth_ultimate.app:app","--host","0.0.0.0","--port","8000"]
EOF

echo ">> tools"
wr tools/make_badge.py <<'EOF'
#!/usr/bin/env python3
import argparse, xml.etree.ElementTree as ET
def read_pct(p):
r=ET.parse(p).getroot()
if 'line-rate' in r.attrib: return float(r.attrib['line-rate'])*100.0
lv=r.attrib.get('lines-valid'); lc=r.attrib.get('lines-covered')
return 100.0*(int(lc)/max(1,int(lv))) if lv and lc else 0.0
def col(p): return "#4c1" if p>=95 else "#97CA00" if p>=90 else "#dfb317"
SVG='''<svg xmlns="http://www.w3.org/2000/svg" width="150" height="20"><rect width="80" height="20" fill="#555"/><rect x="80" width="70" height="20" fill="{c}"/><g fill="#fff" font-family="DejaVu Sans,Verdana,sans-serif" font-size="11"><text x="40" y="14" text-anchor="middle">coverage</text><text x="115" y="14" text-anchor="middle">{p:.1f}%</text></g></svg>'''
if __name__=="__main__":
ap=argparse.ArgumentParser(); ap.add_argument("--xml",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
pct=read_pct(a.xml); open(a.out,"w").write(SVG.format(p=pct,c=col(pct)))
EOF
chmod +x tools/make_badge.py

echo ">> workflows"
wr .github/workflows/ci.yml <<'EOF'
name: CI
on: { push: { branches: [ main ] }, pull_request: { branches: [ main ] } }
permissions: { contents: read }
env: { COV_MIN: "90" }
jobs:
test:
runs-on: ubuntu-latest
steps:
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
with: { python-version: "3.11" }
- run: python -m pip install -U pip && pip install -e .[test]
- run: pytest --cov --cov-report=xml
- uses: actions/upload-artifact@v4
with: { name: coverage-xml, path: coverage.xml }
EOF

wr .github/workflows/release-on-tag.yml <<'EOF'
name: Release on Tag
on: { push: { tags: [ "*" ] } }
permissions: { contents: write, packages: write }
jobs:
release:
runs-on: ubuntu-latest
steps:
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
with: { python-version: "3.11" }
- run: python -m pip install -U pip && pip install -e .[test] && pip install build && pytest --cov --cov-report=xml && python -m build
- uses: softprops/action-gh-release@v2
with: { generate_release_notes: true, files: |-
dist/__
coverage.xml }
env: { GITHUB_TOKEN: ${GITHUB_TOKEN} }
EOF

wr .github/workflows/pages.yml <<'EOF'
name: Pages (Coverage + OpenAPI + Demo)
on: { push: { branches: [ main ] }, workflow_dispatch: {} }
permissions: { contents: read, pages: write, id-token: write }
concurrency: { group: "pages", cancel-in-progress: true }
jobs:
build-and-deploy:
runs-on: ubuntu-latest
steps:
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
with: { python-version: "3.11" }
- run: python -m pip install -U pip && pip install -e .[test] && pytest --cov --cov-report=xml
- run: mkdir -p site/badges site/openapi && python tools/make_badge.py --xml coverage.xml --out site/badges/coverage.svg && cp openapi/openapi.yaml site/openapi/openapi.yaml
- run: |
cat > site/openapi.html <<'HTML' <!doctype html><html><head><meta charset="utf-8"/> <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script> <title>FactSynth API</title></head><body><redoc spec-url="./openapi/openapi.yaml"></redoc></body></html>
HTML
cat > site/index.html <<'HTML' <!doctype html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/> <title>FactSynth — Live Demo</title></head><body> <h1>FactSynth — Live Demo</h1><p>API: <code id="apiBase"></code></p> <textarea id="prompt" rows="6" cols="80">hello world</textarea><br/> <input id="max" type="number" value="5" min="1"/><button id="run">Generate</button> <pre id="out"></pre><p>Coverage: <img src="./badges/coverage.svg"/></p><p><a href="./openapi.html">OpenAPI Docs</a></p> <script>
function q(n){return new URLSearchParams(location.search).get(n)}
const API = q('api') || (location.origin.includes('github.io') ? '' : location.origin);
document.getElementById('apiBase').textContent = API || '(set ?api=https://host)';
document.getElementById('run').onclick = async ()=>{
const prompt=document.getElementById('prompt').value; const max=parseInt(document.getElementById('max').value||'5',10);
const out=document.getElementById('out'); out.textContent='...';
try{ const r=await fetch((API||'')+'/v1/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt,max_tokens:max})});
const j=await r.json().catch(async()=>({raw:await r.text()})); out.textContent=JSON.stringify(j,null,2);
}catch(e){ out.textContent='Request failed: '+e; } }; </script></body></html>
HTML
- uses: actions/configure-pages@v5
- uses: actions/upload-pages-artifact@v3
with: { path: "./site" }
- uses: actions/deploy-pages@v4
EOF

wr .github/workflows/codeql.yml <<'EOF'
name: CodeQL
on: { push: { branches: [ main ] }, pull_request: { branches: [ main ] }, schedule: [ { cron: "27 3 * * 3" } ] }
permissions: { contents: read, security-events: write }
jobs:
analyze:
runs-on: ubuntu-latest
steps:
- uses: actions/checkout@v4
- uses: github/codeql-action/init@v3
with: { languages: python }
- uses: github/codeql-action/autobuild@v3
- uses: github/codeql-action/analyze@v3
EOF

wr .github/dependabot.yml <<'EOF'
version: 2
updates:

* package-ecosystem: "github-actions"
  directory: "/"
  schedule: { interval: "daily", time: "04:00" }
* package-ecosystem: "pip"
  directory: "/"
  schedule: { interval: "daily", time: "04:30" }
  open-pull-requests-limit: 10
EOF

echo ">> done"
