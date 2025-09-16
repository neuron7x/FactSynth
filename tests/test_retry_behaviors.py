from unittest.mock import AsyncMock

import pytest
from httpx import ConnectError

from factsynth_ultimate.api import routers


@pytest.mark.anyio
async def test_delay_jitter(monkeypatch):
    client = AsyncMock()
    client.post.side_effect = ConnectError("fail")

    ctx = AsyncMock()
    ctx.__aenter__.return_value = client
    ctx.__aexit__.return_value = None

    monkeypatch.setattr(routers.httpx, "AsyncClient", lambda **_: ctx)

    sleep_mock = AsyncMock()
    monkeypatch.setattr(routers, "_sleep", sleep_mock)

    factor = 1.1
    monkeypatch.setattr(routers.random, "uniform", lambda _a, _b: factor)

    await routers._post_callback(
        "http://cb", {}, attempts=2, base_delay=1.0, max_delay=2.0
    )

    sleep_mock.assert_awaited_once()
    assert sleep_mock.await_args.args[0] == factor
    ctx.__aenter__.assert_awaited_once()
    ctx.__aexit__.assert_awaited_once()


@pytest.mark.anyio
async def test_retry_respects_max_elapsed(monkeypatch):
    client = AsyncMock()
    client.post.side_effect = ConnectError("fail")

    ctx = AsyncMock()
    ctx.__aenter__.return_value = client
    ctx.__aexit__.return_value = None

    monkeypatch.setattr(routers.httpx, "AsyncClient", lambda **_: ctx)

    current_time = 0.0

    def monotonic():
        return current_time

    sleep_calls = []

    async def fake_sleep(s: float):
        nonlocal current_time
        sleep_calls.append(s)
        current_time += s

    monkeypatch.setattr(routers.time, "monotonic", monotonic)
    monkeypatch.setattr(routers, "_sleep", fake_sleep)

    factor = 1.5
    monkeypatch.setattr(routers.random, "uniform", lambda _a, _b: factor)

    await routers._post_callback(
        "http://cb",
        {},
        attempts=10,
        base_delay=0.5,
        max_delay=5.0,
        max_elapsed=1.0,
    )

    expected_attempts = 2
    expected_sleeps = [0.75, 0.25]
    assert client.post.await_count == expected_attempts
    assert sleep_calls == expected_sleeps
    ctx.__aenter__.assert_awaited_once()
    ctx.__aexit__.assert_awaited_once()
