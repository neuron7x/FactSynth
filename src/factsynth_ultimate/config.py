"""Persistent configuration helpers for command-line utilities."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_ENV_VAR = "FACTSYNTH_CONFIG_PATH"
DEFAULT_CONFIG_DIR = Path.home() / ".factsynth"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.json"


class ConfigError(RuntimeError):
    """Raised when the configuration file cannot be parsed."""


@dataclass
class Config:
    """Application configuration persisted on disk."""

    CALLBACK_URL_ALLOWED_HOSTS: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable representation of the config."""

        return {"CALLBACK_URL_ALLOWED_HOSTS": list(self.CALLBACK_URL_ALLOWED_HOSTS)}


def config_path() -> Path:
    """Return the path to the configuration file."""

    override = os.environ.get(CONFIG_ENV_VAR)
    if override:
        return Path(override)
    return DEFAULT_CONFIG_PATH


def load_config(path: Path | None = None) -> Config:
    """Load :class:`Config` from ``path`` or the default location."""

    cfg_path = Path(path) if path is not None else config_path()
    if not cfg_path.exists():
        return Config()
    try:
        raw = json.loads(cfg_path.read_text())
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ConfigError(f"Failed to parse configuration: {cfg_path}") from exc

    hosts_raw = raw.get("CALLBACK_URL_ALLOWED_HOSTS", [])
    if hosts_raw is None:
        items: list[Any] = []
    elif isinstance(hosts_raw, str):
        items = [part for part in (segment.strip() for segment in hosts_raw.split(",")) if part]
    elif isinstance(hosts_raw, Iterable):
        items = list(hosts_raw)
    else:  # pragma: no cover - defensive
        raise ConfigError("CALLBACK_URL_ALLOWED_HOSTS must be a list or string")

    parsed_hosts = _normalize_hosts(items)
    return Config(CALLBACK_URL_ALLOWED_HOSTS=parsed_hosts)


def save_config(config: Config, path: Path | None = None) -> Path:
    """Persist ``config`` to disk and return the path used."""

    cfg_path = Path(path) if path is not None else config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = _normalize_hosts(config.CALLBACK_URL_ALLOWED_HOSTS)
    payload = {"CALLBACK_URL_ALLOWED_HOSTS": normalized}
    cfg_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return cfg_path


def add_callback_host(host: str, path: Path | None = None) -> Config:
    """Add ``host`` to the callback allowlist stored at ``path``."""

    config = load_config(path)
    updated_hosts = _normalize_hosts(list(config.CALLBACK_URL_ALLOWED_HOSTS) + [host])
    config.CALLBACK_URL_ALLOWED_HOSTS = updated_hosts
    save_config(config, path)
    return config


def _normalize_hosts(hosts: Iterable[Any]) -> list[str]:
    """Return a sorted, deduplicated list of normalised hosts."""

    seen: set[str] = set()
    cleaned: list[str] = []
    for raw in hosts:
        if raw is None:
            continue
        text = str(raw).strip().lower()
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    cleaned.sort()
    return cleaned


__all__ = [
    "Config",
    "ConfigError",
    "add_callback_host",
    "config_path",
    "load_config",
    "save_config",
]
