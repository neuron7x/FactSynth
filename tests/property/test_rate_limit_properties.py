import pytest

from factsynth_ultimate.core import rate_limit

try:
    from hypothesis import HealthCheck, given, settings
    from hypothesis import strategies as st
except ModuleNotFoundError:  # pragma: no cover - optional
    pytest.skip("hypothesis not installed", allow_module_level=True)


pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


class FakeRedis:
    """Minimal async Redis stub with TTL support."""

    def __init__(self, now):
        self._now = now
        self._data = {}
        self._expiry = {}

    async def hgetall(self, key: str):
        self._maybe_expire(key)
        return self._data.get(key, {}).copy()

    async def hset(self, key: str, mapping):
        self._maybe_expire(key)
        encoded = {k: str(v) for k, v in mapping.items()}
        self._data.setdefault(key, {}).update(encoded)

    async def expire(self, key: str, ttl: int):
        self._expiry[key] = self._now() + ttl

    def _maybe_expire(self, key: str):
        exp = self._expiry.get(key)
        if exp is not None and self._now() >= exp:
            self._data.pop(key, None)
            self._expiry.pop(key, None)


@pytest.mark.anyio
@settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    events=st.lists(
        st.tuples(
            st.floats(min_value=0.0, max_value=5.0),
            st.integers(min_value=1, max_value=5),
        ),
        min_size=1,
        max_size=20,
    )
)
async def test_rate_limit_properties(monkeypatch, events):
    burst = 5
    sustain = 1.0
    ttl = 10
    current_time = 0.0

    def fake_time():
        return current_time

    monkeypatch.setattr(rate_limit.time, "time", fake_time)

    redis = FakeRedis(fake_time)
    quota = rate_limit.RateQuota(burst, sustain)
    rl = rate_limit.RateLimitMiddleware(
        lambda *a, **k: None,
        redis=redis,
        api=quota,
        ip=quota,
        org=quota,
        ttl=ttl,
    )

    tokens = burst
    key = "k"
    for delta, count in events:
        current_time += delta
        tokens = min(burst, tokens + delta * sustain)
        for _ in range(count):
            allowed_expected = tokens >= 1
            tokens_expected = tokens - 1 if allowed_expected else tokens
            allowed, remaining = await rl._take(key, quota)
            assert allowed == allowed_expected
            assert remaining == pytest.approx(tokens_expected)
            assert 0 <= remaining <= burst
            tokens = tokens_expected

    current_time += ttl + 1
    allowed, remaining = await rl._take(key, quota)
    assert allowed is True
    assert remaining == pytest.approx(burst - 1)
