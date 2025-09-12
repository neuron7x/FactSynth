import os

import pytest

try:
    import schemathesis
    from schemathesis import openapi

    from factsynth_ultimate.app import create_app
except ModuleNotFoundError as e:  # pragma: no cover - dependency missing in some envs
    pytest.skip(f"Missing dependency: {e}", allow_module_level=True)
_ = schemathesis

API_KEY = os.getenv("API_KEY", "change-me")

schema = openapi.from_asgi("/openapi.json", create_app(), headers={"x-api-key": API_KEY})
schema.validate()


def test_openapi_schema_has_operations() -> None:
    assert list(schema.get_all_operations())
