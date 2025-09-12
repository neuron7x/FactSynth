from http import HTTPStatus

from fastapi.testclient import TestClient

from factsynth_ultimate.app import app


def test_score_validation_ok() -> None:
    c = TestClient(app)
    r = c.post(
        "/v1/score",
        headers={"x-api-key": "change-me"},
        json={"text": "hello", "targets": ["hello"]},
    )
    assert r.status_code == HTTPStatus.OK


def test_413_large_payload() -> None:
    c = TestClient(app)
    big = "x" * (2_100_000)
    r = c.post("/v1/score", headers={"x-api-key": "change-me"}, json={"text": big})
    assert r.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    body = r.json()
    trace_id = body.pop("trace_id")
    assert trace_id
    assert body["type"] == "about:blank"
    assert body["title"] == "Payload Too Large"
    assert body["status"] == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    assert "exceeds limit of 2000000 bytes" in body["detail"]
