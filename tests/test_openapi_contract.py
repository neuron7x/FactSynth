import os
import pathlib

import pytest

requests = pytest.importorskip("requests")

schemathesis = pytest.importorskip("schemathesis")
from schemathesis import openapi  # noqa: E402

BASE_URL = os.getenv("FACTSYNTH_BASE_URL", "http://127.0.0.1:8000")
OPENAPI_PATH = os.getenv("FACTSYNTH_OPENAPI", "openapi/openapi.yaml")
API_KEY = os.getenv("API_KEY", "change-me")

openapi_file = pathlib.Path(OPENAPI_PATH)
if not openapi_file.exists():
    pytest.skip("OpenAPI spec not found; add openapi/openapi.yaml to enable contract tests", allow_module_level=True)

schema = openapi.from_path(OPENAPI_PATH)
schema.validate()
if not list(schema.get_all_operations()):
    pytest.skip(
        "OpenAPI spec has no operations; contract tests skipped",
        allow_module_level=True,
    )

@schema.parametrize()
def test_api_conforms(case):
    if case.path not in ["/v1/healthz", "/metrics", "/v1/version"]:
        case.headers = {**(case.headers or {}), "x-api-key": API_KEY}
    try:
        response = case.call(base_url=BASE_URL)
    except requests.exceptions.RequestException:
        pytest.skip("Could not connect to API; skipping contract tests due to connectivity issues")
    case.validate_response(response)
