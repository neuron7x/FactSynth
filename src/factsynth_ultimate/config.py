"""Persistent configuration helpers for command-line utilities."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Mapping
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
    RETRIEVER_NAME: str | None = None
    RETRIEVER_OPTIONS: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable representation of the config."""

        payload: dict[str, Any] = {
            "CALLBACK_URL_ALLOWED_HOSTS": _normalize_hosts(
                self.CALLBACK_URL_ALLOWED_HOSTS
            ),
        }
        if name := _normalize_retriever_name(self.RETRIEVER_NAME):
            payload["RETRIEVER_NAME"] = name
        if self.RETRIEVER_OPTIONS:
            payload["RETRIEVER_OPTIONS"] = _normalize_retriever_options(
                self.RETRIEVER_OPTIONS
            )
        return payload


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

    retriever_name = _normalize_retriever_name(raw.get("RETRIEVER_NAME"))
    retriever_options = _normalize_retriever_options(
        raw.get("RETRIEVER_OPTIONS", {}),
        strict=True,
    )

    return Config(
        CALLBACK_URL_ALLOWED_HOSTS=parsed_hosts,
        RETRIEVER_NAME=retriever_name,
        RETRIEVER_OPTIONS=retriever_options,
    )


def save_config(config: Config, path: Path | None = None) -> Path:
    """Persist ``config`` to disk and return the path used."""

    cfg_path = Path(path) if path is not None else config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    payload = config.to_dict()
    cfg_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return cfg_path


def add_callback_host(host: str, path: Path | None = None) -> Config:
    """Add ``host`` to the callback allowlist stored at ``path``."""

    config = load_config(path)
    updated_hosts = _normalize_hosts(list(config.CALLBACK_URL_ALLOWED_HOSTS) + [host])
    config.CALLBACK_URL_ALLOWED_HOSTS = updated_hosts
    save_config(config, path)
    return config


def remove_callback_host(host: str, path: Path | None = None) -> Config:
    """Remove ``host`` from the callback allowlist stored at ``path``."""

    config = load_config(path)
    if not config.CALLBACK_URL_ALLOWED_HOSTS:
        return config

    targets = set(_normalize_hosts([host]))
    if not targets:
        return config

    remaining = [item for item in config.CALLBACK_URL_ALLOWED_HOSTS if item not in targets]
    config.CALLBACK_URL_ALLOWED_HOSTS = _normalize_hosts(remaining)
    save_config(config, path)
    return config


def set_callback_hosts(hosts: Iterable[Any], path: Path | None = None) -> Config:
    """Replace the callback allowlist with ``hosts`` at ``path``."""

    config = load_config(path)
    config.CALLBACK_URL_ALLOWED_HOSTS = _normalize_hosts(hosts)
    save_config(config, path)
    return config


def configure_retriever(
    name: str,
    *,
    options: Mapping[str, Any] | None = None,
    path: Path | None = None,
    merge: bool = False,
) -> Config:
    """Set the active retriever and optionally update its options."""

    normalized = _normalize_retriever_name(name)
    if not normalized:
        raise ConfigError("Retriever name must not be empty")

    config = load_config(path)
    previous = config.RETRIEVER_NAME
    config.RETRIEVER_NAME = normalized

    if merge and normalized == previous:
        merged = dict(config.RETRIEVER_OPTIONS)
        if options:
            merged.update(_normalize_retriever_options(options, strict=True))
        config.RETRIEVER_OPTIONS = merged
    else:
        if options is None:
            config.RETRIEVER_OPTIONS = {}
        else:
            config.RETRIEVER_OPTIONS = _normalize_retriever_options(
                options,
                strict=True,
            )

    save_config(config, path)
    return config


def clear_retriever(path: Path | None = None) -> Config:
    """Remove the active retriever configuration."""

    config = load_config(path)
    config.RETRIEVER_NAME = None
    config.RETRIEVER_OPTIONS = {}
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


def _normalize_retriever_name(raw: Any) -> str | None:
    """Return a stripped retriever name or ``None`` if not set."""

    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _normalize_retriever_options(
    options: Any,
    *,
    strict: bool = False,
) -> dict[str, Any]:
    """Normalize retriever option mappings."""

    if options is None:
        return {}
    if isinstance(options, Mapping):
        iterable = options.items()
    elif isinstance(options, Iterable) and not isinstance(options, (str, bytes)):
        iterable = options
    else:
        if strict:
            raise ConfigError("RETRIEVER_OPTIONS must be a mapping")
        return {}

    cleaned: dict[str, Any] = {}
    for key, value in iterable:
        normalized_key = _normalize_retriever_name(key)
        if not normalized_key:
            continue
        cleaned[normalized_key] = value
    return cleaned


__all__ = [
    "Config",
    "ConfigError",
    "add_callback_host",
    "configure_retriever",
    "clear_retriever",
    "remove_callback_host",
    "set_callback_hosts",
    "config_path",
    "load_config",
    "save_config",
]
