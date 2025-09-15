from http import HTTPStatus

import pytest

EXPECTED_METRICS = [
    "factsynth_requests_total",
    "factsynth_request_latency_seconds_bucket",
    "factsynth_scoring_seconds_bucket",
    "factsynth_sse_tokens_total",
    "factsynth_rate_limit_blocks_total",
    "factsynth_explanation_satisfaction_score_bucket",
    "factsynth_citation_precision_bucket",
]


@pytest.mark.anyio
async def test_prometheus_metrics_exposed(client, httpx_mock):
    httpx_mock.reset()
    httpx_mock.assert_all_responses_were_requested = False
    r = await client.get("/metrics")
    assert r.status_code == HTTPStatus.OK
    text = r.text
    for metric in EXPECTED_METRICS:
        assert metric in text
