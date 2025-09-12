import pytest

try:
    import schemathesis
except ModuleNotFoundError as e:  # pragma: no cover - dependency missing in some envs
    pytest.skip(f"Missing dependency: {e}", allow_module_level=True)

OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "stub", "version": "0.1.0"},
    "paths": {"/v1/score": {"post": {"responses": {"200": {"description": "OK"}}}}},
}

schema = schemathesis.from_dict(OPENAPI_SPEC, base_url="http://test")
schema.validate()


def test_openapi_schema_has_operations() -> None:
    assert list(schema.get_all_operations())
