from fastapi.testclient import TestClient

from factsynth_ultimate.app import create_app
from factsynth_ultimate.core.metrics import SSE_TOKENS


def test_stream_sse_client_disconnect() -> None:
    text = " ".join(str(i) for i in range(1000))
    total_tokens = 1000
    initial = SSE_TOKENS._value.get()
    with TestClient(create_app()) as client, client.stream(
        "POST",
        "/v1/stream",
        headers={"x-api-key": "change-me"},
        json={"text": text},
    ):
        # Do not consume the stream to simulate client disconnect.
        pass
    diff = SSE_TOKENS._value.get() - initial
    assert diff < total_tokens
