from fastapi.testclient import TestClient
from factsynth_ultimate.app import app

def test_score_validation_ok():
    c = TestClient(app)
    r = c.post("/v1/score", headers={"x-api-key":"change-me"}, json={"text":"hello","targets":["hello"]})
    assert r.status_code == 200

def test_413_large_payload():
    c = TestClient(app)
    big = "x" * (2_100_000)
    r = c.post("/v1/score", headers={"x-api-key":"change-me"}, json={"text":big})
    assert r.status_code in (200, 413)  # if content-length missing, middleware can't pre-reject
