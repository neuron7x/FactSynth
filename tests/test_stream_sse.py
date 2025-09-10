from http import HTTPStatus

from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app
from factsynth_ultimate.core.metrics import SSE_TOKENS


def test_stream_sse() -> None:
    initial = SSE_TOKENS._value.get()
    with TestClient(create_app()) as client, client.stream(
        "POST", "/v1/stream", headers={"x-api-key": "change-me"}, json={"text": "abc"}
    ) as r:
        body = b"".join(r.iter_bytes())
        status = r.status_code
    assert status == HTTPStatus.OK
    assert b"event: start" in body and b"event: end" in body
    tokens = body.count(b"event: token")
    assert SSE_TOKENS._value.get() - initial == tokens
