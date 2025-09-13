import pytest

from factsynth_ultimate.core import secrets


def test_validate_key_prod(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    with pytest.raises(RuntimeError):
        secrets._validate_key("")
    monkeypatch.setenv("ENV", "dev")
    assert secrets._validate_key("abc") == "abc"


def test_read_api_key_file(tmp_path, monkeypatch):
    fp = tmp_path / "key.txt"
    fp.write_text("filekey", encoding="utf-8")
    monkeypatch.setenv("KEY_FILE", str(fp))
    key = secrets.read_api_key("KEY_ENV", "KEY_FILE", None, "unused")
    assert key == "filekey"


def test_read_api_key_env(monkeypatch):
    monkeypatch.delenv("KEY_FILE", raising=False)
    monkeypatch.setenv("KEY_ENV", "envkey")
    key = secrets.read_api_key("KEY_ENV", "KEY_FILE", None, "unused")
    assert key == "envkey"


def test_read_api_key_default(monkeypatch):
    monkeypatch.delenv("KEY_FILE", raising=False)
    monkeypatch.delenv("KEY_ENV", raising=False)
    key = secrets.read_api_key("KEY_ENV", "KEY_FILE", "def", "unused")
    assert key == "def"


def test_read_api_key_vault(monkeypatch):
    class DummyClient:
        def __init__(self, url, token):
            pass

        class secrets:
            class kv:
                class v2:
                    @staticmethod
                    def read_secret_version(path):
                        _ = path
                        return {"data": {"data": {"API": "vaultkey"}}}

    class DummyHVAC:
        Client = DummyClient

    monkeypatch.setattr(secrets, "hvac", DummyHVAC)
    monkeypatch.setenv("VAULT_ADDR", "x")
    monkeypatch.setenv("VAULT_TOKEN", "y")
    monkeypatch.setenv("VAULT_PATH", "z")
    key = secrets.read_api_key("MISSING", "MISSING_FILE", None, "API")
    assert key == "vaultkey"
    monkeypatch.delenv("VAULT_ADDR")
    monkeypatch.delenv("VAULT_TOKEN")
    monkeypatch.delenv("VAULT_PATH")


def test_read_api_key_vault_error(monkeypatch, caplog):
    class DummyClient:
        def __init__(self, url, token):
            _ = url, token

        class secrets:
            class kv:
                class v2:
                    @staticmethod
                    def read_secret_version(path):
                        _ = path
                        raise secrets.VaultError("boom")

    class DummyHVAC:
        Client = DummyClient

    monkeypatch.setattr(secrets, "hvac", DummyHVAC)
    monkeypatch.setenv("VAULT_ADDR", "x")
    monkeypatch.setenv("VAULT_TOKEN", "y")
    monkeypatch.setenv("VAULT_PATH", "z")
    monkeypatch.setenv("KEY_ENV", "envkey")
    with caplog.at_level("ERROR"):
        key = secrets.read_api_key("KEY_ENV", "MISSING_FILE", None, "API")
    assert key == "envkey"
    assert "Vault lookup failed" in caplog.text
    monkeypatch.delenv("VAULT_ADDR")
    monkeypatch.delenv("VAULT_TOKEN")
    monkeypatch.delenv("VAULT_PATH")
    monkeypatch.delenv("KEY_ENV")
