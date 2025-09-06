from fastapi.testclient import TestClient
from src.factsynth_ultimate.api import app


def test_endpoints_ok():
    H = {"x-api-key": "change-me", "content-type": "application/json"}
    with TestClient(app) as client:
        r = client.get("/v1/healthz")
        assert r.status_code == 200
        r2 = client.post("/v1/intent_reflector", headers=H, json={"intent": "Тест", "length": 100})
        assert r2.status_code == 200 and "text" in r2.json()
