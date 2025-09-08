from __future__ import annotations

_MESSAGES = {
    "Too Many Requests": {"uk": "Забагато запитів"},
    "Forbidden": {"uk": "Заборонено"},
}


def translate(message: str, accept_language: str | None) -> str:
    """Return localized message based on Accept-Language header."""
    if not accept_language:
        return message
    lang = accept_language.split(",", 1)[0].split("-", 1)[0].lower()
    return _MESSAGES.get(message, {}).get(lang, message)
