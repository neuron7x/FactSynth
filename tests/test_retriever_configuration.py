from importlib import metadata
from pathlib import Path

import pytest

from factsynth_ultimate.cli import main as fsctl_main
from factsynth_ultimate.config import configure_retriever, load_config
from factsynth_ultimate.services.retrievers.registry import load_configured_retriever
from factsynth_ultimate.services.retrievers.plugins.elasticsearch import (
    ElasticSearchRetriever,
)

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def _install_entry_points(monkeypatch, entry_points: list[metadata.EntryPoint]) -> None:
    """Patch :mod:`importlib.metadata` to return ``entry_points``."""

    def fake_entry_points(*args, **kwargs):  # type: ignore[override]
        if hasattr(metadata, "EntryPoints"):
            return metadata.EntryPoints(entry_points)
        grouped: dict[str, list[metadata.EntryPoint]] = {}
        for ep in entry_points:
            grouped.setdefault(ep.group, []).append(ep)
        return grouped

    monkeypatch.setattr(metadata, "entry_points", fake_entry_points)


def _elasticsearch_entry_point() -> metadata.EntryPoint:
    return metadata.EntryPoint(
        name="elasticsearch",
        value=(
            "factsynth_ultimate.services.retrievers.plugins.elasticsearch:"
            "create_elasticsearch_retriever"
        ),
        group="factsynth.retrievers",
    )


def test_configure_retriever_sets_name_and_options(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.json"

    configure_retriever(
        "elasticsearch",
        options={"host": "http://es:9200", "timeout": 2},
        path=cfg_path,
    )

    config = load_config(cfg_path)
    assert config.RETRIEVER_NAME == "elasticsearch"
    assert config.RETRIEVER_OPTIONS == {"host": "http://es:9200", "timeout": 2}


def test_configure_retriever_merge_preserves_existing(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.json"

    configure_retriever(
        "elasticsearch",
        options={"host": "http://es:9200", "timeout": 2},
        path=cfg_path,
    )

    configure_retriever(
        "elasticsearch",
        options={"index": "facts"},
        path=cfg_path,
        merge=True,
    )

    config = load_config(cfg_path)
    assert config.RETRIEVER_NAME == "elasticsearch"
    assert config.RETRIEVER_OPTIONS == {
        "host": "http://es:9200",
        "timeout": 2,
        "index": "facts",
    }


def test_load_configured_retriever_instantiates_plugin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_path = tmp_path / "config.json"
    ep = _elasticsearch_entry_point()
    _install_entry_points(monkeypatch, [ep])

    configure_retriever(
        "elasticsearch",
        options={"host": "http://es:9200", "index": "facts"},
        path=cfg_path,
    )

    retriever = load_configured_retriever(cfg_path)
    assert isinstance(retriever, ElasticSearchRetriever)
    assert retriever.host == "http://es:9200"
    assert retriever.index == "facts"

    docs = retriever.search("test", k=1)
    assert docs
    assert "ElasticSearch[facts]" in docs[0].text


def test_cli_retriever_workflow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    cfg_path = tmp_path / "config.json"
    ep = _elasticsearch_entry_point()
    _install_entry_points(monkeypatch, [ep])

    exit_code = fsctl_main(
        [
            "--config",
            str(cfg_path),
            "retriever",
            "set",
            "elasticsearch",
            "--option",
            "host=http://es:9200",
            "--option",
            "timeout=2",
        ]
    )
    assert exit_code == 0
    capsys.readouterr()

    config = load_config(cfg_path)
    assert config.RETRIEVER_NAME == "elasticsearch"
    assert config.RETRIEVER_OPTIONS == {"host": "http://es:9200", "timeout": 2}

    exit_code = fsctl_main(["--config", str(cfg_path), "retriever", "show"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Active retriever: elasticsearch" in output
    assert "http://es:9200" in output

    exit_code = fsctl_main(["--config", str(cfg_path), "retriever", "list"])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "elasticsearch" in output

    exit_code = fsctl_main(["--config", str(cfg_path), "retriever", "clear"])
    assert exit_code == 0
    config = load_config(cfg_path)
    assert config.RETRIEVER_NAME is None
    assert config.RETRIEVER_OPTIONS == {}
