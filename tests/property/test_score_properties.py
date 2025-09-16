from http import HTTPStatus

import pytest
from httpx import AsyncClient, MockTransport, Response
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


def _pick_score(payload):
    if isinstance(payload, dict):
        for k in ("coverage", "score"):
            if k in payload and isinstance(payload[k], int | float):
                return float(payload[k])
        if "data" in payload and isinstance(payload["data"], dict):
            for k in ("coverage", "score"):
                if k in payload["data"] and isinstance(payload["data"][k], int | float):
                    return float(payload["data"][k])
    return None


async def _assert_monotonic_coverage(api_client: AsyncClient, base_headers, query, base, extra):
    A = base
    B = base + [e for e in extra if e not in base]

    r1 = await api_client.post("/v1/score", headers=base_headers, json={"query": query, "facts": A})
    r2 = await api_client.post("/v1/score", headers=base_headers, json={"query": query, "facts": B})

    if HTTPStatus.NOT_FOUND in {r1.status_code, r2.status_code}:
        raise AssertionError(
            "score endpoint '/v1/score' is unavailable (received HTTP 404). "
            f"statuses: first={r1.status_code} second={r2.status_code}"
        )

    payload1 = r1.json()
    payload2 = r2.json()

    s1 = _pick_score(payload1)
    s2 = _pick_score(payload2)

    if s1 is None or s2 is None:
        raise AssertionError(
            "score response payload missing numeric 'score' or 'coverage' fields. "
            f"payload1={payload1!r} payload2={payload2!r}"
        )

    EPS = 1e-9
    assert s2 + EPS >= s1, f"non-monotone coverage: |A|={len(A)} |B|={len(B)} => {s1} -> {s2}"


@pytest.mark.anyio
@settings(
    max_examples=40, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    query=st.text(min_size=5, max_size=80),
    base=st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=4, unique=True),
    extra=st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=3, unique=True),
)
async def test_score_monotonic_coverage(api_stub, base_headers, query, base, extra):
    await _assert_monotonic_coverage(api_stub, base_headers, query, base, extra)


@pytest.mark.anyio
async def test_score_monotonic_coverage_fails_when_endpoint_missing(base_headers):
    """Ensure the test suite fails fast when /v1/score is unavailable."""

    def handler(_request):
        return Response(status_code=HTTPStatus.NOT_FOUND)

    transport = MockTransport(handler)
    async with AsyncClient(transport=transport, base_url="http://test") as failing_client:
        with pytest.raises(AssertionError, match=r"score endpoint '/v1/score' is unavailable"):
            await _assert_monotonic_coverage(
                failing_client,
                base_headers,
                "guard query",
                ["fact"],
                ["extra"],
            )
