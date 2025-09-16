import logging

import pytest

from factsynth_ultimate.core import secrets

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


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
                    def read_secret_version(path, **_kwargs):  # noqa: ANN001
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


def test_read_api_key_vault_logs_error(monkeypatch, caplog):
    class DummyClient:
        def __init__(self, url, token):
            pass

        class secrets:
            class kv:
                class v2:
                    @staticmethod
                    def read_secret_version(path, **_kwargs):  # noqa: ANN001
                        _ = path
                        raise secrets.VaultError("fail")

    class DummyHVAC:
        Client = DummyClient

    monkeypatch.setattr(secrets, "hvac", DummyHVAC)
    monkeypatch.setenv("VAULT_ADDR", "x")
    monkeypatch.setenv("VAULT_TOKEN", "y")
    monkeypatch.setenv("VAULT_PATH", "z")

    with caplog.at_level(logging.WARNING):
        secrets.read_api_key("MISSING", "MISSING_FILE", None, "API")

    assert any(
        r.levelno == logging.WARNING and "Vault error" in r.message and "fail" in r.message
        for r in caplog.records
    )
