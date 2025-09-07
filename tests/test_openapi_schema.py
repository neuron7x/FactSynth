import os, pytest

def test_openapi_schema_valid_if_present():
    p = "openapi/openapi.yaml"
    if not os.path.exists(p):
        pytest.skip("No openapi spec")
    try:
        import yaml
        from openapi_spec_validator import validate_spec
    except Exception:
        pytest.skip("validators not installed")
    with open(p, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    validate_spec(spec)
