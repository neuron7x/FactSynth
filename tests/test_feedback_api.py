from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


def test_feedback_roundtrip() -> None:
    client = TestClient(app)
    r = client.post(
        "/v1/feedback",
        json={"session_id": "s1", "request_id": "r1", "rating": 5, "comment": "ok"},
    )
    assert r.status_code == 201  # noqa: PLR2004
    data = client.get("/v1/feedback?limit=1").json()
    assert data["items"][0]["rating"] == 5  # noqa: PLR2004
