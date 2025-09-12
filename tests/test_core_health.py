import socket

from factsynth_ultimate.core import health


def test_parse_valid_and_invalid():
    assert health._parse("localhost:80") == ("localhost", 80)
    assert health._parse("[::1]:443") == ("::1", 443)
    assert health._parse("bad") is None
    assert health._parse("x:99999") is None


def test_tcp_check(monkeypatch):
    class DummySock:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_create_connection(addr, timeout=1.5):
        _ = timeout
        if addr == ("ok", 1):
            return DummySock()
        raise OSError

    monkeypatch.setattr(socket, "create_connection", fake_create_connection)
    assert health.tcp_check("ok", 1)
    assert not health.tcp_check("fail", 1)


def test_multi_tcp_check(monkeypatch):
    def fake_tcp(host, _port, _timeout=1.5):
        return host == "up"

    monkeypatch.setattr(health, "tcp_check", fake_tcp)
    result = health.multi_tcp_check(["up:80", "bad", "down:81"])
    assert result == {"up:80": True, "bad": False, "down:81": False}
