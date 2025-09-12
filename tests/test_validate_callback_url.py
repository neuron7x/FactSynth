from factsynth_ultimate.api.routers import validate_callback_url


def test_validate_callback_url_basic():
    assert validate_callback_url("https://example.com")
    assert not validate_callback_url("ftp://example.com")


def test_validate_callback_url_allowed_hosts(monkeypatch):
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "a.com,b.com")
    assert validate_callback_url("https://a.com/path")
    assert not validate_callback_url("https://c.com")
