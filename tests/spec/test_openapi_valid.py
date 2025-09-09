import pathlib, pytest
try:
    from openapi_spec_validator import validate_spec
    from openapi_spec_validator.readers import read_from_filename
except Exception:
    validate_spec = None

SPEC_PATHS = [
    pathlib.Path("openapi/openapi.yaml"),
    pathlib.Path("openapi/openapi.yml"),
    pathlib.Path("openapi.yaml"),
    pathlib.Path("openapi.yml"),
]

def _find_spec():
    for p in SPEC_PATHS:
        if p.is_file():
            return str(p)
    return None

@pytest.mark.skipif(_find_spec() is None, reason="OpenAPI spec not found")
def test_openapi_schema_valid():
    assert validate_spec is not None, "openapi-spec-validator not installed"
    url, spec_dict = read_from_filename(_find_spec())
    validate_spec(spec_dict)
