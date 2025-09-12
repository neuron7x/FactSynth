"""Simple helpers for language negotiation and translation."""

from __future__ import annotations

from fastapi import Request

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "internal_server_error": "Internal Server Error",
        "payload_too_large": "Payload Too Large",
        "forbidden": "Forbidden",
        "unauthorized": "Unauthorized",
        "too_many_requests": "Too Many Requests",
    },
    "uk": {
        "internal_server_error": "Внутрішня помилка сервера",
        "payload_too_large": "Занадто великий запит",
        "forbidden": "Заборонено",
        "unauthorized": "Неавторизовано",
        "too_many_requests": "Забагато запитів",
    },
}

DEFAULT_LANG = "en"
SUPPORTED_LANGS = set(MESSAGES.keys())


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
    """Return a localized message for ``key`` in the desired language."""

    return MESSAGES.get(lang, MESSAGES[DEFAULT_LANG]).get(
        key, MESSAGES[DEFAULT_LANG].get(key, key)
    )
