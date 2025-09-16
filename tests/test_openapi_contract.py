import os

import pytest
from httpx import AsyncClient

try:
    import schemathesis
except ModuleNotFoundError as e:  # pragma: no cover - dependency missing in some envs
    pytest.skip(f"Missing dependency: {e}", allow_module_level=True)

from factsynth_ultimate.app import create_app
from hypothesis import settings

if not hasattr(schemathesis, "from_uri"):
    schemathesis.from_uri = schemathesis.openapi.from_asgi  # type: ignore[attr-defined]

pytestmark = [
    pytest.mark.httpx_mock(assert_all_responses_were_requested=False),
    pytest.mark.contract,
]

API_KEY = os.getenv("API_KEY", "change-me")
DEFAULT_CONTRACT_HEADERS = {
    "x-api-key": API_KEY,
    "content-type": "application/json",
}


async def _load_openapi_document(
    client: AsyncClient, *, headers: dict[str, str] | None = None
) -> dict:
    response = await client.get("/openapi.json", headers=headers)
    response.raise_for_status()
    return response.json()


@pytest.fixture()
async def openapi_schema(
    client: AsyncClient, base_headers: dict[str, str]
) -> schemathesis.BaseSchema:
    document = await _load_openapi_document(client, headers=base_headers)
    schema = schemathesis.openapi.from_dict(document)
    schema.validate()
    return schema


SCHEMA_FROM_URI = schemathesis.from_uri(
    "/openapi.json", app=create_app(), headers=DEFAULT_CONTRACT_HEADERS
)
SCHEMA_FROM_URI.validate()


@pytest.mark.anyio
async def test_openapi_schema_has_operations(openapi_schema: schemathesis.BaseSchema) -> None:
    assert list(openapi_schema.get_all_operations())


@SCHEMA_FROM_URI.parametrize()
@settings(deadline=None, max_examples=1)
def test_openapi_contract(case: schemathesis.Case, base_headers: dict[str, str]) -> None:
    response = case.call(headers=base_headers)
    assert response.status_code < 500
