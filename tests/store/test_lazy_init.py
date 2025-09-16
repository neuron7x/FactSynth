from __future__ import annotations

from factsynth_ultimate.store import (
    STORE_ACTIVE_BACKEND,
    STORE_CONNECT_ATTEMPTS,
    STORE_CONNECT_RETRIES,
    StoreFactory,
)


def _sample(metric, labels):
    wrapper = metric.labels(**labels)
    return float(wrapper._value.get())


def test_factory_connects_lazily():
    calls: list[object] = []

    def builder() -> object:
        calls.append(object())
        return calls[-1]

    factory = StoreFactory("lazy", builder, retry_delay=0.0)

    assert not calls
    assert factory.is_connected is False

    attempts_before = _sample(STORE_CONNECT_ATTEMPTS, {"store": "lazy"})
    retries_before = _sample(STORE_CONNECT_RETRIES, {"store": "lazy"})

    first = factory.get()
    assert calls == [first]
    assert factory.is_connected is True
    assert factory.backend == type(first).__name__

    second = factory.get()
    assert second is first
    assert calls == [first]

    attempts_after = _sample(STORE_CONNECT_ATTEMPTS, {"store": "lazy"})
    retries_after = _sample(STORE_CONNECT_RETRIES, {"store": "lazy"})
    backend_label = {"store": "lazy", "backend": type(first).__name__}
    backend_gauge = _sample(STORE_ACTIVE_BACKEND, backend_label)

    assert attempts_after == attempts_before + 1
    assert retries_after == retries_before
    assert backend_gauge == 1.0

    factory.close()
    assert factory.is_connected is False
    assert _sample(STORE_ACTIVE_BACKEND, backend_label) == 0.0

    factory.get()
    assert len(calls) == 2
