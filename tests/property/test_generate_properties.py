import math
from collections import Counter
from http import HTTPStatus

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


def _pick_text(payload):
    if isinstance(payload, dict):
        for k in ("text",):
            if k in payload and isinstance(payload[k], str):
                return payload[k]
        if "output" in payload and isinstance(payload["output"], dict) and "text" in payload["output"]:
            return payload["output"]["text"]
        if "data" in payload and isinstance(payload["data"], dict) and "text" in payload["data"]:
            return payload["data"]["text"]
    return None


def _entropy_bits_per_char(s: str) -> float:
    if not s:
        return 0.0
    cnt = Counter(s)
    n = len(s)
    probs = [c / n for c in cnt.values()]
    return -sum(p * math.log2(p) for p in probs)


@pytest.mark.anyio
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(text=st.text(alphabet=st.characters(blacklist_categories=("Cs",)), min_size=5, max_size=120))
async def test_generate_entropy_and_length_stability(client, base_headers, text):
    r1 = await client.post("/v1/generate", headers=base_headers, json={"text": text, "seed": 42})
    r2 = await client.post("/v1/generate", headers=base_headers, json={"text": text, "seed": 42})

    if HTTPStatus.NOT_FOUND in {r1.status_code, r2.status_code}:
        pytest.skip("generate endpoint not available")

    assert r1.status_code < HTTPStatus.INTERNAL_SERVER_ERROR
    assert r2.status_code < HTTPStatus.INTERNAL_SERVER_ERROR
    t1 = _pick_text(r1.json()) or ""
    t2 = _pick_text(r2.json()) or ""
    assert len(t1) == len(t2)

    H = _entropy_bits_per_char(t1)
    ENTROPY_MIN = 0.4
    ENTROPY_MAX = 6.5
    assert ENTROPY_MIN <= H <= ENTROPY_MAX, f"Entropy out of bounds: {H:.2f} bits/char"


@pytest.mark.anyio
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(text=st.text(min_size=10, max_size=200))
async def test_generate_nonempty_output(client, base_headers, text):
    r = await client.post("/v1/generate", headers=base_headers, json={"text": text})
    if r.status_code == HTTPStatus.NOT_FOUND:
        pytest.skip("generate endpoint not available")
    assert r.status_code < HTTPStatus.INTERNAL_SERVER_ERROR
    out = _pick_text(r.json())
    assert isinstance(out, str) and len(out.strip()) > 0
