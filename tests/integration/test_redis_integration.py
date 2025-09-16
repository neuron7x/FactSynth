"""Redis integration tests that exercise basic CRUD operations."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from redis import Redis
from redis.exceptions import RedisError


def _should_run() -> bool:
    flag = os.getenv("RUN_REDIS_INTEGRATION_TESTS", "").strip().lower()
    return flag in {"1", "true", "yes", "on"}


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _should_run(), reason="RUN_REDIS_INTEGRATION_TESTS is not enabled"),
]


def _create_client() -> Redis:
    redis_url = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )


@pytest.fixture()
def redis_client() -> Generator[Redis, None, None]:
    client = _create_client()
    try:
        client.ping()
    except RedisError as exc:  # pragma: no cover - integration only
        pytest.skip(f"Redis is unavailable: {exc}")
    client.flushdb()
    try:
        yield client
    finally:
        try:
            client.flushdb()
        finally:
            client.close()


def test_set_and_get(redis_client: Redis) -> None:
    key = "user:1:name"
    value = "Ada"

    status = redis_client.set(key, value)
    assert status is True
    assert redis_client.get(key) == value


def test_update_existing_key(redis_client: Redis) -> None:
    counter_key = "visit:counter"

    redis_client.set(counter_key, 1)
    redis_client.incrby(counter_key, 2)

    assert redis_client.get(counter_key) == "3"


def test_delete_key(redis_client: Redis) -> None:
    session_key = "session:active"

    redis_client.set(session_key, "yes")
    removed = redis_client.delete(session_key)

    assert removed == 1
    assert redis_client.exists(session_key) == 0


def test_hash_operations(redis_client: Redis) -> None:
    profile_key = "profile:42"

    redis_client.hset(profile_key, mapping={"name": "Ada", "role": "admin"})
    redis_client.hset(profile_key, "role", "maintainer")

    assert redis_client.hgetall(profile_key) == {"name": "Ada", "role": "maintainer"}
