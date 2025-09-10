import pytest

from factsynth_ultimate.app import create_app
from factsynth_ultimate.core.secrets import read_api_key


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


@pytest.mark.parametrize("api_key", [None, "", "change-me"])
def test_read_api_key_prod_requires_real_key(monkeypatch, api_key):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.delenv("API_KEY_FILE", raising=False)
    if api_key is None:
        monkeypatch.delenv("API_KEY", raising=False)
    else:
        monkeypatch.setenv("API_KEY", api_key)
    with pytest.raises(RuntimeError):
        read_api_key("API_KEY", "API_KEY_FILE", "change-me", "API_KEY")
