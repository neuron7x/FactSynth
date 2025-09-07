#!/usr/bin/env python3
import sys
from pathlib import Path

def main():
    path = Path("openapi/openapi.yaml")
    if not path.exists():
        print("No openapi/openapi.yaml; skip validation.")
        return 0
    try:
        import yaml  # type: ignore
        from openapi_spec_validator import validate_spec
    except Exception:
        print("Install validators: pip install pyyaml openapi-spec-validator", file=sys.stderr)
        return 1
    with path.open("r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    validate_spec(spec)
    print("OpenAPI spec valid.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
