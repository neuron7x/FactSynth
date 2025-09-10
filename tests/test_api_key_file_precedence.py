import pytest

from factsynth_ultimate.core.secrets import read_api_key


def test_read_api_key_prefers_file(monkeypatch, tmp_path):
    path = tmp_path / "key.txt"
    path.write_text("file-key", encoding="utf-8")
    monkeypatch.setenv("API_KEY_FILE", str(path))
    monkeypatch.setenv("API_KEY", "env-key")
    assert read_api_key("API_KEY", "API_KEY_FILE", None, "API_KEY") == "file-key"


def test_read_api_key_missing_file_error(monkeypatch, tmp_path):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.delenv("API_KEY", raising=False)
    path = tmp_path / "missing.txt"
    monkeypatch.setenv("API_KEY_FILE", str(path))
    with pytest.raises((FileNotFoundError, RuntimeError)):
        read_api_key("API_KEY", "API_KEY_FILE", None, "API_KEY")
