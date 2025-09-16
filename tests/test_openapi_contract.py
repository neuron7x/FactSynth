import pytest

schemathesis = pytest.importorskip("schemathesis")

try:  # pragma: no cover - exercised in environments with newer Schemathesis
    _from_dict = schemathesis.from_dict  # type: ignore[attr-defined]
except AttributeError:  # pragma: no branch
    _from_dict = schemathesis.openapi.from_dict

pytestmark = [
    pytest.mark.httpx_mock(assert_all_responses_were_requested=False),
    pytest.mark.anyio,
]


async def test_openapi_schema_has_operations(client, base_headers) -> None:
    response = await client.get("/openapi.json", headers=base_headers)
    assert response.status_code == 200, response.text

    raw_schema = response.json()
    schema = _from_dict(raw_schema)
    schema.validate()

    operations = [result.ok() for result in schema.get_all_operations()]
    assert operations, "OpenAPI contract must define operations"
    assert any(
        operation.path == "/v1/score" and operation.method.upper() == "POST"
        for operation in operations
    ), "Score endpoint is missing from the OpenAPI contract"
