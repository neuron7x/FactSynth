import pytest

from factsynth_ultimate.app import create_app


@pytest.mark.parametrize("api_key", [None, "", "change-me"])
def test_prod_env_requires_real_api_key(monkeypatch, api_key):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.delenv("API_KEY_FILE", raising=False)
    if api_key is None:
        monkeypatch.delenv("API_KEY", raising=False)
    else:
        monkeypatch.setenv("API_KEY", api_key)
    with pytest.raises(RuntimeError):
        create_app()
