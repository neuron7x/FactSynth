import json
import logging
from io import StringIO
from http import HTTPStatus

import httpx

from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app


def test_internal_error_logs_json_with_request_id():
    app = create_app()

    @app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    handler = logging.getLogger().handlers[0]
    stream = StringIO()
    orig_stream = handler.stream
    handler.stream = stream
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            r = client.get(
                "/boom", headers={"x-api-key": "change-me", "x-request-id": "RID-1"}
            )
            assert r.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
            body = r.json()
            trace_id = body.pop("trace_id")
            assert trace_id == "RID-1"
            assert body == {
                "type": "about:blank",
                "title": "Internal Server Error",
                "status": HTTPStatus.INTERNAL_SERVER_ERROR,
                "detail": "boom",
            }
    finally:
        handler.stream = orig_stream

    lines = [ln for ln in stream.getvalue().splitlines() if "/boom" in ln]
    assert lines, "no log line captured"
    record = json.loads(lines[0])
    assert record["request_id"] == "RID-1"
    assert record["message"].startswith("Unhandled exception on /boom")

    # make a dummy HTTP call so the httpx_mock autouse fixture is satisfied
    httpx.post("http://test/v1/score", json={"text": "x"})
