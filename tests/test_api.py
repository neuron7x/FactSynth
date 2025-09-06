from fastapi.testclient import TestClient

from src.factsynth_ultimate.api import create_app
from src.factsynth_ultimate.config import FSUConfig
from src.factsynth_ultimate.settings import Settings


def test_endpoints_ok():
    cfg = FSUConfig(start_phrase="Старт")
    settings = Settings(API_KEY="secret")
    app = create_app(cfg=cfg, settings=settings)
    client = TestClient(app)
    headers = {"x-api-key": settings.API_KEY, "content-type": "application/json"}

    r = client.get("/v1/healthz")
    assert r.status_code == 200

    r2 = client.post(
        "/v1/intent_reflector",
        headers=headers,
        json={"intent": "Тест", "length": 10},
    )
    assert r2.status_code == 200
    assert r2.json()["text"].startswith(cfg.start_phrase)

