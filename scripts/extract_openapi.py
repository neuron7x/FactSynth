#!/usr/bin/env python3
import os, json, sys, importlib, pathlib, contextlib, urllib.request
from pathlib import Path
outdir = Path("openapi"); outdir.mkdir(exist_ok=True, parents=True)
dst_json = outdir/"openapi.json"; dst_yaml = outdir/"openapi.yaml"

def write(obj):
    dst_json.write_text(json.dumps(obj, indent=2))
    try:
        import yaml
        dst_yaml.write_text(yaml.safe_dump(obj, sort_keys=False))
    except Exception:
        pass

# 1) If OPENAPI_URL is set, fetch
u = os.getenv("OPENAPI_URL")
if u:
    with urllib.request.urlopen(u, timeout=10) as r:
        write(json.loads(r.read().decode()))
    sys.exit(0)

# 2) Try FastAPI auto-discovery
candidates = [
    ("app", "app"), ("src.app", "app"),
    ("api", "app"), ("factsynth.app", "app")
]
for mod, attr in candidates:
    with contextlib.suppress(Exception):
        m = importlib.import_module(mod)
        app = getattr(m, attr)
        if hasattr(app, "openapi"):
            write(app.openapi()); sys.exit(0)

# 3) If openapi files already exist, do nothing
for p in (outdir/"openapi.yaml", outdir/"openapi.yml", outdir/"openapi.json"):
    if p.exists(): sys.exit(0)

print("Could not extract OpenAPI; set OPENAPI_URL or expose FastAPI app.", file=sys.stderr)
sys.exit(0)
