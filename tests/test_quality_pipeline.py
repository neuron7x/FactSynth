from http import HTTPStatus

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from factsynth_ultimate.api import verify as verify_mod
from factsynth_ultimate.core.factsynth_lock import FactSynthLock

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)

app = FastAPI()
app.include_router(verify_mod.api)
client = TestClient(app)


def test_quality_pipeline_verify_returns_lock():
    payload = {
        "claim": "The earth orbits the sun",
        "lock": {
            "verdict": {"decision": "supported"},
            "evidence": [{"source": "url", "content": "text"}],
        },
    }

    resp = client.post("/verify", json=payload)
    assert resp.status_code == HTTPStatus.OK

    returned = FactSynthLock.model_validate(resp.json())
    expected = FactSynthLock.model_validate(payload["lock"])
    assert returned == expected
