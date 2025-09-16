import logging
from http import HTTPStatus

import pytest

from factsynth_ultimate.cli import main as fsctl_main
from factsynth_ultimate.config import Config, load_config, save_config
from factsynth_ultimate.api.routers import get_allowed_hosts, reload_allowed_hosts
from factsynth_ultimate.validators.callback import validate_callback_url


def test_cli_callbacks_allow_persists_host(tmp_path, capsys):
    config_file = tmp_path / "config.json"

    exit_code = fsctl_main(["--config", str(config_file), "callbacks", "allow", "Example.com"])

    assert exit_code == 0
    cfg = load_config(config_file)
    assert cfg.CALLBACK_URL_ALLOWED_HOSTS == ["example.com"]
    output = capsys.readouterr().out
    assert "example.com" in output
    assert "Current callback allowlist" in output


def test_cli_callbacks_allow_deduplicates(tmp_path):
    config_file = tmp_path / "config.json"
    fsctl_main(["--config", str(config_file), "callbacks", "allow", "example.com"])
    fsctl_main(["--config", str(config_file), "callbacks", "allow", "EXAMPLE.com"])

    cfg = load_config(config_file)
    assert cfg.CALLBACK_URL_ALLOWED_HOSTS == ["example.com"]


def test_cli_callbacks_remove_updates_allowlist(tmp_path):
    config_file = tmp_path / "config.json"
    fsctl_main(["--config", str(config_file), "callbacks", "allow", "example.com"])

    exit_code = fsctl_main(["--config", str(config_file), "callbacks", "remove", "example.com"])

    assert exit_code == 0
    cfg = load_config(config_file)
    assert cfg.CALLBACK_URL_ALLOWED_HOSTS == []


def test_cli_callbacks_list_shows_current_allowlist(tmp_path, capsys):
    config_file = tmp_path / "config.json"

    fsctl_main(["--config", str(config_file), "callbacks", "list"])
    output = capsys.readouterr().out
    assert "<empty>" in output

    fsctl_main(["--config", str(config_file), "callbacks", "allow", "example.com"])
    fsctl_main(["--config", str(config_file), "callbacks", "list"])
    output = capsys.readouterr().out
    assert "example.com" in output


@pytest.mark.parametrize(
    ("url", "allowed", "expect_problem", "expected_reason"),
    [
        ("https://example.com/cb", ["example.com"], False, None),
        ("https://evil.com/cb", ["example.com"], True, "host_not_allowed"),
        ("https://example.com/cb", [], True, "allowlist_empty"),
    ],
)
def test_validate_callback_url_allowlist(url, allowed, expect_problem, expected_reason, caplog):
    caplog.set_level(logging.WARNING)
    caplog.clear()
    problem = validate_callback_url(url, allowed)
    assert (problem is not None) is expect_problem
    if problem:
        assert "callback" in problem.detail.lower()
        assert problem.extras["reason"] == expected_reason
        records = [record for record in caplog.records if record.name == "factsynth_ultimate.validators.callback"]
        assert records, "expected validation to emit log record"
        logged = records[-1].problem_details
        assert logged["extras"]["reason"] == expected_reason
    else:
        assert not [
            record
            for record in caplog.records
            if record.name == "factsynth_ultimate.validators.callback"
        ]


@pytest.mark.anyio
async def test_api_callbacks_allowlist_crud(client, base_headers, tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    monkeypatch.setenv("FACTSYNTH_CONFIG_PATH", str(config_file))
    reload_allowed_hosts()
    try:
        response = await client.get("/v1/callbacks/allowlist", headers=base_headers)
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"hosts": []}

        response = await client.post(
            "/v1/callbacks/allowlist",
            headers=base_headers,
            json={"host": "Example.com"},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"hosts": ["example.com"]}

        response = await client.put(
            "/v1/callbacks/allowlist",
            headers=base_headers,
            json={"hosts": ["Another.com", "Example.com"]},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"hosts": ["another.com", "example.com"]}

        response = await client.delete(
            "/v1/callbacks/allowlist/example.com", headers=base_headers
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"hosts": ["another.com"]}

        cfg = load_config(config_file)
        assert cfg.CALLBACK_URL_ALLOWED_HOSTS == ["another.com"]
        assert list(get_allowed_hosts()) == ["another.com"]
    finally:
        reload_allowed_hosts()


def test_settings_respects_saved_allowlist(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    save_config(Config(CALLBACK_URL_ALLOWED_HOSTS=["example.com"]), config_file)
    monkeypatch.setenv("FACTSYNTH_CONFIG_PATH", str(config_file))

    from factsynth_ultimate.core.settings import Settings

    settings = Settings()
    assert settings.callback_url_allowed_hosts == ["example.com"]
