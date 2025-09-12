from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from factsynth_ultimate.core.body_limit import BodySizeLimitMiddleware


def create_app(max_bytes: int) -> TestClient:
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=max_bytes)

    @app.post("/echo")
    async def echo(request: Request):
        data = await request.body()
        return {"len": len(data)}

    return TestClient(app)


def test_body_limit_rejects_payload() -> None:
    with create_app(5) as client:
        r = client.post("/echo", data="x" * 10)
        assert r.status_code == 413
        assert r.json()["status"] == 413


def test_body_limit_allows_payload() -> None:
    with create_app(100) as client:
        r = client.post("/echo", data="hello")
        assert r.status_code == 200
        assert r.json() == {"len": 5}
