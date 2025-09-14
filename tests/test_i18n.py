from __future__ import annotations

import json

import yaml
from fastapi import Request

from factsynth_ultimate import i18n


def load_locale(lang: str) -> dict[str, str]:
    path = i18n.LOCALES_DIR / f"{lang}.json"
    if path.exists():
        return json.loads(path.read_text())
    path = i18n.LOCALES_DIR / f"{lang}.yaml"
    return yaml.safe_load(path.read_text())


def make_request(header: str) -> Request:
    scope = {"type": "http", "headers": [(b"accept-language", header.encode())]}
    return Request(scope)


def test_choose_language(httpx_mock):
    httpx_mock.reset()
    req = make_request("fr, uk;q=0.8, en;q=0.5")
    assert i18n.choose_language(req) == "uk"
    req2 = make_request("")
    assert i18n.choose_language(req2) == i18n.DEFAULT_LANG
    req3 = make_request("uk;q=bogus, en;q=0.5")
    assert i18n.choose_language(req3) == i18n.DEFAULT_LANG
    req4 = make_request("*, fr")
    assert i18n.choose_language(req4) == i18n.DEFAULT_LANG


def test_translate(httpx_mock):
    httpx_mock.reset()
    uk_catalog = load_locale("uk")
    en_catalog = load_locale("en")
    assert i18n.translate("uk", "forbidden") == uk_catalog["forbidden"]
    assert i18n.translate("xx", "forbidden") == en_catalog["forbidden"]
    assert i18n.translate("uk", "only_en") == en_catalog["only_en"]
    assert i18n.translate("uk", "missing_key") == "missing_key"
