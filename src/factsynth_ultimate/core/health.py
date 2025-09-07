from __future__ import annotations
import socket, re
from typing import Iterable

_HOST_RE = re.compile(r"""
    ^
    (?:\[(?P<ipv6>[^]]+)\]|(?P<host>[^:]+))   # [::1] або hostname
    :(?P<port>\d{1,5})
    $
""", re.X)

def _parse(item: str) -> tuple[str, int] | None:
    m = _HOST_RE.match(item.strip())
    if not m: return None
    host = m.group("ipv6") or m.group("host")
    port = int(m.group("port"))
    if not (1 <= port <= 65535): return None
    return host, port

def tcp_check(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

def multi_tcp_check(items: Iterable[str]) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for raw in items:
        parsed = _parse(raw)
        if not parsed:
            results[raw] = False
            continue
        host, port = parsed
        results[raw] = tcp_check(host, port)
    return results
