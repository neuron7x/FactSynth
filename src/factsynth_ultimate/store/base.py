"""Helpers for building and managing storage backends."""

from __future__ import annotations

import inspect
import logging
import time
from collections.abc import Callable
from typing import Generic, TypeVar

from prometheus_client import Counter, Gauge


__all__ = [
    "STORE_ACTIVE_BACKEND",
    "STORE_CONNECT_ATTEMPTS",
    "STORE_CONNECT_FAILURES",
    "STORE_CONNECT_RETRIES",
    "STORE_SWITCHES",
    "StoreFactory",
]


_T = TypeVar("_T")


STORE_CONNECT_ATTEMPTS = Counter(
    "factsynth_store_connect_attempts_total",
    "Attempts to connect a store backend",
    ("store",),
)

STORE_CONNECT_FAILURES = Counter(
    "factsynth_store_connect_failures_total",
    "Failed attempts to connect a store backend",
    ("store",),
)

STORE_CONNECT_RETRIES = Counter(
    "factsynth_store_connect_retries_total",
    "Retries performed while connecting a store backend",
    ("store",),
)

STORE_SWITCHES = Counter(
    "factsynth_store_switch_total",
    "Number of times an active store backend changed",
    ("store", "backend"),
)

STORE_ACTIVE_BACKEND = Gauge(
    "factsynth_store_active_backend",
    "Indicator of the currently active store backend",
    ("store", "backend"),
)


class StoreFactory(Generic[_T]):
    """Factory that lazily creates and manages store backends."""

    def __init__(
        self,
        name: str,
        builder: Callable[[], _T],
        *,
        max_attempts: int = 3,
        retry_delay: float = 0.1,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        if max_attempts < 1:
            msg = "max_attempts must be at least 1"
            raise ValueError(msg)
        self._name = name
        self._builder = builder
        self._max_attempts = max_attempts
        self._retry_delay = max(0.0, retry_delay)
        self._sleep = sleep or time.sleep
        self._store: _T | None = None
        self._backend_label: str | None = None
        self._logger = logging.getLogger(__name__)

    @property
    def name(self) -> str:
        """Return the logical name of the factory."""

        return self._name

    @property
    def backend(self) -> str | None:
        """Return the label for the currently active backend."""

        return self._backend_label

    @property
    def is_connected(self) -> bool:
        """Return ``True`` when a backend has been initialized."""

        return self._store is not None

    def configure(self, builder: Callable[[], _T]) -> None:
        """Update the builder used to construct new backends."""

        self._builder = builder

    def get(self) -> _T:
        """Return the active backend, connecting lazily on first use."""

        if self._store is None:
            return self.connect()
        return self._store

    def connect(self, *, force: bool = False) -> _T:
        """Initialize the backend, retrying on transient failures."""

        if self._store is not None and not force:
            return self._store
        if force and self._store is not None:
            self.close()

        last_exc: Exception | None = None
        attempt = 0
        while attempt < self._max_attempts:
            attempt += 1
            STORE_CONNECT_ATTEMPTS.labels(self._name).inc()
            try:
                store = self._builder()
            except Exception as exc:  # pragma: no cover - defensive guard
                last_exc = exc
                STORE_CONNECT_FAILURES.labels(self._name).inc()
                if attempt < self._max_attempts:
                    STORE_CONNECT_RETRIES.labels(self._name).inc()
                    self._logger.warning(
                        "Failed to initialize %s backend (attempt %s/%s): %s",
                        self._name,
                        attempt,
                        self._max_attempts,
                        exc,
                    )
                    if self._retry_delay:
                        self._sleep(self._retry_delay)
                    continue
                self._logger.error(
                    "Unable to initialize %s backend after %s attempts", self._name, attempt, exc_info=exc
                )
                raise
            else:
                backend = type(store).__name__
                previous = self._backend_label
                self._store = store
                self._backend_label = backend
                STORE_ACTIVE_BACKEND.labels(self._name, backend).set(1)
                if previous and previous != backend:
                    STORE_ACTIVE_BACKEND.labels(self._name, previous).set(0)
                    STORE_SWITCHES.labels(self._name, backend).inc()
                return store

        if last_exc is not None:  # pragma: no cover - safeguard
            raise last_exc
        msg = "Failed to initialize store backend"
        raise RuntimeError(msg)

    def reconnect(self) -> _T:
        """Rebuild the backend, forcing a reconnect."""

        self.close()
        return self.connect(force=True)

    def close(self) -> None:
        """Close the active backend if one is connected."""

        store = self._store
        if store is None:
            return
        self._store = None
        backend = self._backend_label
        if backend:
            STORE_ACTIVE_BACKEND.labels(self._name, backend).set(0)

        close = getattr(store, "close", None)
        if callable(close):
            try:
                close()
            except Exception:  # pragma: no cover - defensive guard
                self._logger.warning("Error closing %s backend", self._name, exc_info=True)
                return

        aclose = getattr(store, "aclose", None)
        if callable(aclose):  # pragma: no cover - optional async clean up
            try:
                result = aclose()
                if inspect.isawaitable(result):
                    self._logger.warning(
                        "Async close coroutine returned for %s backend; run in event loop to finalize cleanup",
                        self._name,
                    )
            except Exception:
                self._logger.warning("Error asynchronously closing %s backend", self._name, exc_info=True)
