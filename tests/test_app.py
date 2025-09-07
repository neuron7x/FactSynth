from fastapi.testclient import TestClient
from factsynth_ultimate.app import app


def test_healthz_ok():
    c = TestClient(app)
    r = c.get("/healthz")
    assert r.status_code == 200 and r.json().get("status") == "ok"


def test_metrics_non_empty():
    c = TestClient(app)
    r = c.get("/metrics")
    assert r.status_code == 200 and isinstance(r.text, str) and len(r.text) > 0


def test_generate_basic():
    c = TestClient(app)
    r = c.post("/v1/generate", json={"prompt": "a b c d e", "max_tokens": 3})
    assert r.status_code == 200 and r.json()["output"].startswith("a b c |ck:")
