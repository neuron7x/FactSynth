from __future__ import annotations

import time

from factsynth.core.cache import MemoryBuffer


def test_ttl_expiry() -> None:
    cache = MemoryBuffer(ttl=1)
    cache.set("ns", "k", {"v": 1})
    assert cache.get("ns", "k") == {"v": 1}
    time.sleep(1.2)
    assert cache.get("ns", "k") is None
