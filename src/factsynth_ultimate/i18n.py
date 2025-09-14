"""Minimal internationalisation helpers."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from fastapi import Request

LOCALES_DIR = Path(__file__).parent / "locales"


def _load_catalogs() -> dict[str, dict[str, str]]:
    catalogs: dict[str, dict[str, str]] = {}
    for path in LOCALES_DIR.glob("*"):
        if path.suffix == ".json":
            catalogs[path.stem] = json.loads(path.read_text())
        elif path.suffix in {".yaml", ".yml"}:
            catalogs[path.stem] = yaml.safe_load(path.read_text())
    return catalogs


MESSAGES: dict[str, dict[str, str]] = {}
SUPPORTED_LANGS: set[str] = set()


def refresh_catalogs() -> None:
    """Reload locale catalogs from :data:`LOCALES_DIR`."""
    MESSAGES.clear()
    MESSAGES.update(_load_catalogs())
    SUPPORTED_LANGS.clear()
    SUPPORTED_LANGS.update(MESSAGES.keys())


refresh_catalogs()

DEFAULT_LANG = "en"


def choose_language(request: Request) -> str:
    """Pick best language from ``Accept-Language`` header.

    The header can contain quality values (``q``) which express the
    preference order.  We parse the header into ``(code, q)`` pairs, sort the
    pairs by ``q`` in descending order and return the first base language code
    that is supported.  If no languages match we fall back to
    :data:`DEFAULT_LANG`.
    """

    header = request.headers.get("accept-language", "")
    languages: list[tuple[str, float]] = []
    for part in header.split(","):
        item = part.strip()
        if not item:
            continue
        pieces = [p.strip() for p in item.split(";")]
        code = pieces[0].lower()
        q = 1.0
        for p in pieces[1:]:
            if p.startswith("q="):
                try:
                    q = float(p[2:])
                except ValueError:
                    q = 0.0
                break
        languages.append((code, q))

    for code, _q in sorted(languages, key=lambda item: item[1], reverse=True):
        base = code.split("-")[0]
        if base in SUPPORTED_LANGS:
            return base
    return DEFAULT_LANG


def translate(lang: str, key: str) -> str:
    """Return localized message for given key."""
    return MESSAGES.get(lang, MESSAGES[DEFAULT_LANG]).get(key, MESSAGES[DEFAULT_LANG].get(key, key))
