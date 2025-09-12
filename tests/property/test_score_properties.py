from http import HTTPStatus

import pytest

try:
    from hypothesis import HealthCheck, given, settings
    from hypothesis import strategies as st
except ModuleNotFoundError:  # pragma: no cover - optional
    pytest.skip("hypothesis not installed", allow_module_level=True)


def _pick_score(payload):
    if isinstance(payload, dict):
        for k in ("coverage", "score"):
            if k in payload and isinstance(payload[k], (int, float)):
                return float(payload[k])
        if "data" in payload and isinstance(payload["data"], dict):
            for k in ("coverage", "score"):
                if k in payload["data"] and isinstance(payload["data"][k], (int, float)):
                    return float(payload["data"][k])
    return None


@pytest.mark.anyio
@settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    query=st.text(min_size=5, max_size=80),
    base=st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=4, unique=True),
    extra=st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=3, unique=True),
)
async def test_score_monotonic_coverage(api_stub, base_headers, query, base, extra):
    A = base
    B = base + [e for e in extra if e not in base]

    r1 = await api_stub.post(
        "/v1/score", headers=base_headers, json={"query": query, "facts": A}
    )
    r2 = await api_stub.post(
        "/v1/score", headers=base_headers, json={"query": query, "facts": B}
    )

    if HTTPStatus.NOT_FOUND in {r1.status_code, r2.status_code}:
        pytest.skip("score endpoint not available")

    s1 = _pick_score(r1.json())
    s2 = _pick_score(r2.json())

    if s1 is None or s2 is None:
        pytest.skip("score schema not recognized")

    EPS = 1e-9
    assert s2 + EPS >= s1, f"non-monotone coverage: |A|={len(A)} |B|={len(B)} => {s1} -> {s2}"
