from http import HTTPStatus

from fastapi import HTTPException
from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app


def test_http_exception_returns_problem_json():
    app = create_app()

    @app.get("/http")
    def boom():
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="boom")

    with TestClient(app) as client:
        r = client.get("/http", headers={"x-api-key": "change-me"})
        assert r.status_code == HTTPStatus.BAD_REQUEST
        body = r.json()
        instance = body.pop("instance")
        assert instance
        assert body == {
            "type": "about:blank",
            "title": "Bad Request",
            "status": HTTPStatus.BAD_REQUEST,
            "detail": "boom",
        }


def test_validation_error_returns_problem_json():
    app = create_app()

    @app.get("/validate")
    def validate(q: int) -> int:  # pragma: no cover - FastAPI handles validation
        return q

    with TestClient(app) as client:
        r = client.get("/validate", headers={"x-api-key": "change-me"}, params={"q": "x"})
        assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        body = r.json()
        instance = body.pop("instance")
        assert instance
        assert body["type"] == "about:blank"
        assert body["title"] == "Unprocessable Entity"
        assert body["status"] == HTTPStatus.UNPROCESSABLE_ENTITY
        assert "valid integer" in body["detail"]


def test_unhandled_exception_returns_problem_json():
    app = create_app()

    @app.get("/err")
    def err():
        raise RuntimeError("kapow")

    with TestClient(app, raise_server_exceptions=False) as client:
        r = client.get("/err", headers={"x-api-key": "change-me"})
        assert r.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        body = r.json()
        instance = body.pop("instance")
        assert instance
        assert body == {
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            "detail": "kapow",
        }
