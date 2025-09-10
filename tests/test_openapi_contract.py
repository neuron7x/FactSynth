import os
import pathlib
from pathlib import Path

import pytest

requests = pytest.importorskip("requests")
yaml = pytest.importorskip("yaml")

schemathesis = pytest.importorskip("schemathesis")
from schemathesis import openapi  # noqa: E402

MIN_JUSTIFICATION = 3
MAX_JUSTIFICATION = 7

BASE_URL = os.getenv("FACTSYNTH_BASE_URL", "http://127.0.0.1:8000")
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


def yload(p: str):
    return yaml.safe_load(Path(p).read_text(encoding="utf-8"))


def test_schema_has_contract():
    s = yload("openapi/components/schemas/FactSynthLock_v1_1.yaml")
    fs = s["components"]["schemas"]["FactSynthLock"]
    req = set(fs["required"])
    assert {"verdict", "source_synthesis", "traceability", "recommendations"} <= req

    verdict = fs["properties"]["verdict"]
    assert set(verdict["required"]) == {"status", "confidence", "summary"}
    assert set(verdict["properties"]["status"]["enum"]) == {"SUPPORTED", "REFUTED", "UNCLEAR", "OUT_OF_SCOPE", "ERROR"}

    trace = fs["properties"]["traceability"]["properties"]
    js = trace["justification_steps"]
    assert js["minItems"] == MIN_JUSTIFICATION and js["maxItems"] == MAX_JUSTIFICATION


def test_verify_ref_points_to_schema():
    v = yload("openapi/paths/verify.yaml")
    ref = v["post"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert ref.endswith("#/components/schemas/FactSynthLock")


@schema.parametrize()
def test_api_conforms(case):
    if case.path not in ["/v1/healthz", "/metrics", "/v1/version"]:
        case.headers = {**(case.headers or {}), "x-api-key": API_KEY}
    case.base_url = BASE_URL
    try:
        response = case.call()
    except requests.exceptions.RequestException:
        pytest.skip("Could not connect to API; skipping contract tests due to connectivity issues")
    case.validate_response(response)
