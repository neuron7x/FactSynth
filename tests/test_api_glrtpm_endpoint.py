from http import HTTPStatus

from fastapi import FastAPI
from fastapi.testclient import TestClient

from factsynth_ultimate.api_glrtpm import GLRTPMPipeline, router

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
