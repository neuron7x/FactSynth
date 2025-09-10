import json, asyncio, os, sys
sys.path.insert(0, os.getcwd())
from fastapi.testclient import TestClient
from app.main import app

def test_examples_offline():
    client = TestClient(app)
    with open("tests/factsynth_lock_examples.json","r",encoding="utf-8") as f:
        cases = json.load(f)
    for c in cases:
        r = client.post("/v1/verify",
                        headers={"x-api-key":"key"},
                        json={"claim": c["claim"], "locale":"uk-UA", "max_sources":10})
        assert r.status_code == 200
        data = r.json()
        assert data["verdict"]["status"] in ["SUPPORTED","REFUTED","UNCLEAR","OUT_OF_SCOPE","ERROR"]
        assert 0.0 <= data["verdict"]["confidence"] <= 1.0
        assert isinstance(data["source_synthesis"]["citations"], list)
        # heuristic expectation for fixtures
        assert data["verdict"]["status"] == c["expect_status"]
