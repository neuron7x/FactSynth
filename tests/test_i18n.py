from fastapi import Request

from factsynth_ultimate import i18n


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
    assert i18n.translate("uk", "forbidden") == "Заборонено"
    assert i18n.translate("xx", "forbidden") == "Forbidden"
