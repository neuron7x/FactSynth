import asyncio
import logging
from unittest.mock import AsyncMock

from httpx import ConnectError

from factsynth_ultimate.api import routers


def test_webhook_retry_failure(caplog, monkeypatch):
    client = AsyncMock()
    client.post.side_effect = ConnectError("boom")
    ctx = AsyncMock()
    ctx.__aenter__.return_value = client

    monkeypatch.setattr(routers.httpx, "AsyncClient", lambda **_: ctx)
    monkeypatch.setattr(routers, "_sleep", AsyncMock())

    caplog.set_level(logging.WARNING)
    attempts = 3

    asyncio.run(routers._post_callback("http://cb", {}, attempts=attempts, base_delay=0.0, max_delay=0.0))

    assert client.post.call_count == attempts
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(warnings) == attempts and len(errors) == 1
