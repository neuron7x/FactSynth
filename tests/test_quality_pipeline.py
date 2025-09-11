import json
from http import HTTPStatus
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from factsynth_ultimate.api_akpshi import VerifyReq
from factsynth_ultimate.api_akpshi import verify as verify_fn

pytest.importorskip("numpy")

app = FastAPI()


@app.post("/v1/verify")
def _verify(req: VerifyReq) -> dict:
    return verify_fn(req)


client = TestClient(app)


def load_cases():
    data = json.loads(Path("tests/factsynth_lock_examples.json").read_text())
    for case in data:
        case["payload"] = json.loads((Path("tests") / case["request"]).read_text())
    return data


def test_quality_pipeline_verify():
    for case in load_cases():
        resp = client.post("/v1/verify", json=case["payload"])
        assert resp.status_code == HTTPStatus.OK
        out = resp.json()
        for key, val in case["expected"].items():
            assert out[key] == pytest.approx(val)
