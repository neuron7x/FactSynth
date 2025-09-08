import os
import schemathesis as st

BASE_URL = os.getenv("FACTSYNTH_BASE_URL", "http://127.0.0.1:8000")
OPENAPI_PATH = os.getenv("FACTSYNTH_OPENAPI", "openapi/openapi.yaml")
API_KEY = os.getenv("API_KEY", "change-me")

schema = st.from_path(OPENAPI_PATH).validate()

@schema.parametrize()
def test_api_conforms(case):
    # Apply API key for protected routes
    if case.path not in ["/v1/healthz", "/metrics", "/v1/version"]:
        case.headers = {**(case.headers or {}), "x-api-key": API_KEY}
    case.base_url = BASE_URL
    response = case.call()
    case.validate_response(response)
