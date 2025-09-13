from http import HTTPStatus

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from factsynth_ultimate.api_glrtpm import GLRTPMPipeline, router

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_glrtpm_api(monkeypatch):
    app = FastAPI()
    app.include_router(router)

    def fake_run(_self, thesis: str):
        return {"thesis": thesis}

    monkeypatch.setattr(GLRTPMPipeline, "run", fake_run)
    client = TestClient(app)
    res = client.post("/v1/glrtpm/run", json={"thesis": "x"})
    assert res.status_code == HTTPStatus.OK
    assert res.json() == {"thesis": "x"}
