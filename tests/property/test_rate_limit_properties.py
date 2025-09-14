import pytest

try:
    import fakeredis.aioredis as fakeredis
    from hypothesis import HealthCheck, given, settings
    from hypothesis import strategies as st
except ModuleNotFoundError:  # pragma: no cover - optional
    pytest.skip("fakeredis or hypothesis not installed", allow_module_level=True)

from factsynth_ultimate.core.rate_limit import RateLimitMiddleware


@pytest.mark.anyio
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    ops=st.lists(
        st.tuples(
            st.floats(min_value=0, max_value=5),
            st.integers(min_value=0, max_value=5),
        ),
        min_size=1,
        max_size=10,
    )
)
async def test_take_respects_burst_and_sustain(monkeypatch, ops):
    async def app(scope, receive, send):
        pass

    redis = fakeredis.FakeRedis()
    mw = RateLimitMiddleware(app, redis=redis, burst=5, sustain=1.0)
    redis_key = "rl:test"

    current_time = 0.0

    def fake_time():
        return current_time

    monkeypatch.setattr("factsynth_ultimate.core.rate_limit.time.time", fake_time)

    expected_tokens = mw.burst

    for delta_t, request_count in ops:
        current_time += float(delta_t)
        expected_tokens = min(mw.burst, expected_tokens + delta_t * mw.sustain)
        for _ in range(request_count):
            allowed_expected = expected_tokens >= 1.0
            if allowed_expected:
                expected_tokens -= 1.0
            allowed, tokens = await mw._take(redis_key)
            assert tokens <= mw.burst + 1e-9
            assert allowed is allowed_expected
            assert tokens == pytest.approx(expected_tokens)


@pytest.mark.anyio
async def test_full_recovery_after_pause(monkeypatch):
    async def app(scope, receive, send):
        pass

    redis = fakeredis.FakeRedis()
    burst = 5
    sustain = 1.0
    mw = RateLimitMiddleware(app, redis=redis, burst=burst, sustain=sustain)
    redis_key = "rl:pause"

    current_time = 0.0

    def fake_time():
        return current_time

    monkeypatch.setattr("factsynth_ultimate.core.rate_limit.time.time", fake_time)

    for _ in range(burst):
        allowed, _ = await mw._take(redis_key)
        assert allowed
    allowed, _ = await mw._take(redis_key)
    assert not allowed

    current_time += burst / sustain + 1.0

    for _ in range(burst):
        allowed, _ = await mw._take(redis_key)
        assert allowed
    allowed, _ = await mw._take(redis_key)
    assert not allowed
