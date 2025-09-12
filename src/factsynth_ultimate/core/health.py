"""Helpers for performing basic TCP health checks."""

from __future__ import annotations

import re
import socket
from typing import Iterable

MAX_PORT = 65535

_HOST_RE = re.compile(
    r"""
    ^
    (?:\[(?P<ipv6>[^]]+)\]|(?P<host>[^:]+))   # [::1] or hostname
    :(?P<port>\d{1,5})
    $
    """,
    re.X,
)


def _parse(item: str) -> tuple[str, int] | None:
    """Return ``(host, port)`` extracted from ``item`` or ``None``."""

    m = _HOST_RE.match(item.strip())
    if not m:
        return None
    host = m.group("ipv6") or m.group("host")
    port = int(m.group("port"))
    if not (1 <= port <= MAX_PORT):
        return None
    return host, port


def tcp_check(host: str, port: int, timeout: float = 1.5) -> bool:
    """Attempt a TCP connection to ``host:port``."""

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def multi_tcp_check(items: Iterable[str]) -> dict[str, bool]:
    """Perform :func:`tcp_check` for each entry in ``items``."""

    results: dict[str, bool] = {}
    for raw in items:
        parsed = _parse(raw)
        if not parsed:
            results[raw] = False
            continue
        host, port = parsed
        results[raw] = tcp_check(host, port)
    return results
