from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from factsynth_ultimate.core.request_id import RequestIDMiddleware, get_request_id

def _make_app(header_name: str = "x-request-id") -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware, header_name=header_name)

    @app.get("/")
    async def root(request: Request):
        return {"state": request.state.request_id, "ctx": get_request_id()}

    return app

def test_generates_request_id_when_missing_header():
    app = _make_app()
    client = TestClient(app)

    response = client.get("/")
    data = response.json()
    rid = response.headers["x-request-id"]

    assert rid
    assert data["state"] == rid
    assert data["ctx"] == rid
    assert get_request_id() is None

def test_custom_header_name_preserves_incoming_id():
    header = "x-correlation-id"
    app = _make_app(header)
    client = TestClient(app)

    response = client.get("/", headers={header: "abc"})
    data = response.json()

    assert response.headers[header] == "abc"
    assert data["state"] == "abc"
    assert data["ctx"] == "abc"

def test_get_request_id_resets_between_requests():
    app = _make_app()
    client = TestClient(app)

    first = client.get("/")
    rid1 = first.json()["ctx"]

    assert rid1 == first.headers["x-request-id"]
    assert get_request_id() is None

    second = client.get("/")
    rid2 = second.json()["ctx"]

    assert rid2 == second.headers["x-request-id"]
    assert rid1 != rid2
    assert get_request_id() is None
