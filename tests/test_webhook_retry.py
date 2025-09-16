import logging
from unittest.mock import AsyncMock

import pytest
from httpx import ConnectError

from factsynth_ultimate.api import routers


@pytest.mark.anyio
async def test_webhook_retry_failure(caplog, monkeypatch):
    client = AsyncMock()
    client.post.side_effect = ConnectError("boom")
    ctx = AsyncMock()
    ctx.__aenter__.return_value = client
    ctx.__aexit__.return_value = None

    monkeypatch.setattr(routers.httpx, "AsyncClient", lambda **_: ctx)
    sleep_mock = AsyncMock()
    monkeypatch.setattr(routers, "_sleep", sleep_mock)

    caplog.set_level(logging.WARNING)
    attempts = 3

    await routers._post_callback(
        "http://cb", {}, attempts=attempts, base_delay=0.0, max_delay=0.0
    )

    assert client.post.await_count == attempts
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(warnings) == attempts and len(errors) == 1
    assert sleep_mock.await_count == attempts - 1
    ctx.__aenter__.assert_awaited_once()
    ctx.__aexit__.assert_awaited_once()
