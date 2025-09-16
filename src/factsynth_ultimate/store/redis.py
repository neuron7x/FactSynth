"""Helpers for working with Redis-backed stores."""

from __future__ import annotations

import asyncio
from typing import Any, cast

from redis.asyncio import Redis
from redis.exceptions import RedisError


async def check_health(target: str | Redis | object) -> bool:
    """Return ``True`` when Redis responds to a ping command."""

    if isinstance(target, str):
        client = Redis.from_url(target)
        should_close = True
    else:
        client = cast(Any, target)
        should_close = False

    healthy = False
    try:
        pong: Any
        pong = await client.ping()
        healthy = bool(pong)
    except (RedisError, OSError, asyncio.TimeoutError, AttributeError, TypeError):
        healthy = False
    finally:
        if should_close:
            try:
                await client.aclose()
            except (RedisError, OSError, asyncio.TimeoutError):  # pragma: no cover - defensive
                return False
    return healthy
