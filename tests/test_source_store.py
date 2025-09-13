import time

import fakeredis
import pytest

from factsynth_ultimate.core.source_store import MemorySourceStore, RedisSourceStore


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_memory_store_ttl_cleanup():
    store = MemorySourceStore(ttl=1)
    sid = store.ingest_source("http://example.com", "payload")
    assert store.get_metadata(sid) is not None
    time.sleep(1.1)
    store.cleanup()
    assert store.get_metadata(sid) is None


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_redis_store_persists_entries():
    redis_client = fakeredis.FakeRedis()
    store = RedisSourceStore(redis_client, ttl=None)
    sid = store.ingest_source("http://example.com", "payload")
    new_store = RedisSourceStore(redis_client, ttl=None)
    assert new_store.get_metadata(sid) is not None
