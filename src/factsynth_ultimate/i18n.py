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
        "too_many_requests": "Занадто багато запитів",
    },
}

DEFAULT_LANG = "en"
SUPPORTED_LANGS = set(MESSAGES.keys())


def choose_language(request: Request) -> str:
    """Pick best language from Accept-Language header."""
    header = request.headers.get("accept-language", "")
    for part in header.split(","):
        code = part.split(";")[0].strip().lower()
        if not code:
            continue
        base = code.split("-")[0]
        if base in SUPPORTED_LANGS:
            return base
    return DEFAULT_LANG


def translate(lang: str, key: str) -> str:
    """Return localized message for given key."""
    return MESSAGES.get(lang, MESSAGES[DEFAULT_LANG]).get(
        key, MESSAGES[DEFAULT_LANG].get(key, key)
    )
