import os
import pathlib
from http import HTTPStatus

import pytest

try:
    import schemathesis
    from schemathesis import openapi

    from factsynth_ultimate.app import create_app
    _ = schemathesis
except ModuleNotFoundError as e:
    pytest.skip(f"Missing dependency: {e}", allow_module_level=True)

OPENAPI_PATH = os.getenv("FACTSYNTH_OPENAPI", "openapi/openapi.yaml")
API_KEY = os.getenv("API_KEY", "change-me")

openapi_file = pathlib.Path(OPENAPI_PATH)
if not openapi_file.exists():
    pytest.skip(
        "OpenAPI spec not found; add openapi/openapi.yaml to enable contract tests",
        allow_module_level=True,
    )

schema = openapi.from_path(OPENAPI_PATH)
schema.validate()
if not list(schema.get_all_operations()):
    pytest.skip(
        "OpenAPI spec has no operations; contract tests skipped",
        allow_module_level=True,
    )

app = create_app()


@schema.parametrize()
def test_api_conforms(case):
    if case.path not in ["/v1/healthz", "/metrics", "/v1/version"]:
        case.headers = {**(case.headers or {}), "x-api-key": API_KEY}
    response = case.call(base_url="http://testserver", app=app)
    assert response.status_code < HTTPStatus.INTERNAL_SERVER_ERROR
