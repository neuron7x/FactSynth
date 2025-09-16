from __future__ import annotations

import fakeredis

from factsynth_ultimate.core import source_store
from factsynth_ultimate.core.source_store import (
    MemorySourceStore,
    RedisSourceStore,
    close_store,
    reconnect_store,
)
from factsynth_ultimate.store import STORE_ACTIVE_BACKEND, STORE_SWITCHES


def _sample(metric, labels):
    wrapper = metric.labels(**labels)
    return float(wrapper._value.get())


def test_switch_backend(monkeypatch):
    close_store()
    monkeypatch.setenv("SOURCE_STORE_BACKEND", "memory")
    memory_label = {"store": "source", "backend": "MemorySourceStore"}
    redis_label = {"store": "source", "backend": "RedisSourceStore"}

    store = reconnect_store()
    assert isinstance(store, MemorySourceStore)
    assert _sample(STORE_ACTIVE_BACKEND, memory_label) == 1.0
    assert _sample(STORE_ACTIVE_BACKEND, redis_label) == 0.0

    fake_client = fakeredis.FakeRedis()
    monkeypatch.setenv("SOURCE_STORE_BACKEND", "redis")
    monkeypatch.setattr(source_store.redis, "from_url", lambda url: fake_client)

    switches_before = _sample(STORE_SWITCHES, {"store": "source", "backend": "RedisSourceStore"})
    new_store = reconnect_store()

    assert isinstance(new_store, RedisSourceStore)
    assert new_store.redis is fake_client
    assert _sample(STORE_ACTIVE_BACKEND, memory_label) == 0.0
    assert _sample(STORE_ACTIVE_BACKEND, redis_label) == 1.0
    switches_after = _sample(STORE_SWITCHES, {"store": "source", "backend": "RedisSourceStore"})
    assert switches_after == switches_before + 1

    close_store()
    assert _sample(STORE_ACTIVE_BACKEND, redis_label) == 0.0
