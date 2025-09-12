from factsynth_ultimate.api.routers import validate_callback_url


def test_validate_callback_url(monkeypatch):
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "good.com")
    assert validate_callback_url("https://good.com/cb")
    assert not validate_callback_url("ftp://good.com/cb")
    assert not validate_callback_url("https://evil.com/cb")
    monkeypatch.setenv("CALLBACK_URL_ALLOWED_HOSTS", "")
    assert validate_callback_url("https://whatever.com/cb")
