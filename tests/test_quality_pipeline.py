from http import HTTPStatus
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from factsynth_ultimate.api import verify as verify_mod
from factsynth_ultimate.core.factsynth_lock import FactSynthLock

app = FastAPI()
app.include_router(verify_mod.api)
client = TestClient(app)

def test_quality_pipeline_verify_enriches_lock():
    payload = {
        "claim": "The earth orbits the sun",
        "lock": {
            "verdict": {"decision": "confirmed"},
            "evidence": [{"source_id": "1", "source": "url", "content": "text"}],
        },
    }

    evaluation = {
        "verdict": {"decision": "refuted"},
        "evidence": [
            {
                "source_id": "2",
                "source": "url2",
                "content": "different",
            }
        ],
    }

    with patch("factsynth_ultimate.api.verify.evaluate_claim", return_value=evaluation):
        resp = client.post("/verify", json=payload)

    assert resp.status_code == HTTPStatus.OK

    returned = FactSynthLock.model_validate(resp.json())
    expected = FactSynthLock.model_validate(payload["lock"])
    assert returned != expected
    assert returned.verdict.decision == "refuted"
    assert returned.evidence[0].source_id == "2"
