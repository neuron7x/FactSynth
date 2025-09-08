from http import HTTPStatus

from fastapi.testclient import TestClient

from factsynth_ultimate.app import app


def test_health() -> None:
    client = TestClient(app)
    assert client.get("/v1/healthz").status_code == HTTPStatus.OK
