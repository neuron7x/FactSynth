#!/usr/bin/env python3
import sys
from pathlib import Path

try:
    import yaml
    from openapi_spec_validator import validate_spec
except ImportError:
    yaml = None
    validate_spec = None


def main() -> int:
    path = Path("openapi/openapi.yaml")
    if not path.exists():
        print("No openapi/openapi.yaml; skip validation.")
        return 0
    if yaml is None or validate_spec is None:
        print(
            "Install validators: pip install pyyaml openapi-spec-validator",
            file=sys.stderr,
        )
        return 1
    with path.open("r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    validate_spec(spec)
    print("OpenAPI spec valid.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
