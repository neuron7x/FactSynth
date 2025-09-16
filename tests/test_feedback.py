import re
from http import HTTPStatus

import pytest

@pytest.mark.anyio
async def test_feedback_metrics(client, base_headers, httpx_mock):
    httpx_mock.reset()
    payload = {"explanation_satisfaction": 0.7, "citation_precision": 0.8}
    r = await client.post("/v1/feedback", json=payload, headers=base_headers)
    assert r.status_code == HTTPStatus.OK
    metrics = await client.get("/metrics")
    text = metrics.text
    ess = re.search(r"factsynth_explanation_satisfaction_score_sum\s+([0-9.]+)", text)
    cp = re.search(r"factsynth_citation_precision_sum\s+([0-9.]+)", text)
    assert ess and float(ess.group(1)) >= 0.7
    assert cp and float(cp.group(1)) >= 0.8
