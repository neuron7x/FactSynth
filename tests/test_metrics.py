from http import HTTPStatus

import pytest

EXPECTED_METRICS = [
    "factsynth_requests_total",
    "factsynth_request_latency_seconds_bucket",
    "factsynth_scoring_seconds_bucket",
    "factsynth_sse_tokens_total",
]


@pytest.mark.anyio
async def test_prometheus_metrics_exposed(client):
    r = await client.get("/metrics")
    assert r.status_code == HTTPStatus.OK
    text = r.text
    for metric in EXPECTED_METRICS:
        assert metric in text

