import pytest

schemathesis = pytest.importorskip("schemathesis")

OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "stub", "version": "0.1.0"},
    "paths": {"/v1/score": {"post": {"responses": {"200": {"description": "OK"}}}}},
}

schema = schemathesis.openapi.from_dict(OPENAPI_SPEC)
schema.validate()

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_openapi_schema_has_operations() -> None:
    assert list(schema.get_all_operations())
