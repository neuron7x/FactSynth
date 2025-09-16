import re
from http import HTTPStatus

import pytest

MIN_EXPLANATION_SCORE = 0.7
MIN_CITATION_SCORE = 0.8


@pytest.mark.anyio
async def test_feedback_metrics(client, base_headers, httpx_mock):
    httpx_mock.reset()
    httpx_mock.assert_all_responses_were_requested = False
    payload = {
        "explanation_satisfaction": MIN_EXPLANATION_SCORE,
        "citation_precision": MIN_CITATION_SCORE,
    }
    r = await client.post("/v1/feedback", json=payload, headers=base_headers)
    assert r.status_code == HTTPStatus.OK
    metrics = await client.get("/metrics")
    text = metrics.text
    ess = re.search(r"factsynth_explanation_satisfaction_score_sum\s+([0-9.]+)", text)
    cp = re.search(r"factsynth_citation_precision_sum\s+([0-9.]+)", text)
    assert ess and float(ess.group(1)) >= MIN_EXPLANATION_SCORE
    assert cp and float(cp.group(1)) >= MIN_CITATION_SCORE
