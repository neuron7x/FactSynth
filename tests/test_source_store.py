from datetime import UTC, datetime, timedelta

import fakeredis
import pytest

from factsynth_ultimate.core.source_store import MemorySourceStore, RedisSourceStore


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_memory_store_ttl_cleanup(time_travel):
    store = MemorySourceStore(ttl=1)
    sid = store.ingest_source("http://example.com", "payload", trust=0.9)
    assert store.get_metadata(sid) is not None
    time_travel.shift(1.1)
    assert store.get_metadata(sid) is None


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_redis_store_persists_entries():
    redis_client = fakeredis.FakeRedis()
    store = RedisSourceStore(redis_client, ttl=None)
    sid = store.ingest_source("http://example.com", "payload", trust=0.9)
    new_store = RedisSourceStore(redis_client, ttl=None)
    assert new_store.get_metadata(sid) is not None


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_low_trust_pruned():
    store = MemorySourceStore(min_trust=0.5)
    sid = store.ingest_source("http://example.com", "payload", trust=0.1)
    assert store.get_metadata(sid) is None


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_expired_entry_pruned():
    store = MemorySourceStore()
    expired = datetime.now(UTC) - timedelta(seconds=1)
    sid = store.ingest_source("http://example.com", "payload", trust=0.9, expires_at=expired)
    assert store.get_metadata(sid) is None
