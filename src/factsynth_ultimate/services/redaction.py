from __future__ import annotations

"""Utilities for removing personally identifiable information from text."""

import re

# Regular expressions covering common PII patterns
_EMAIL_RE = re.compile(r"\b[\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def redact_pii(text: str) -> str:
    """Replace common PII patterns in *text* with placeholders.

    Parameters
    ----------
    text:
        The input string that may contain PII.

    Returns
    -------
    str
        ``text`` with e-mail addresses, phone numbers and social security
        numbers replaced by redaction tokens.
    """

    text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = _PHONE_RE.sub("[REDACTED_PHONE]", text)
    text = _SSN_RE.sub("[REDACTED_SSN]", text)
    return text


__all__ = ["redact_pii"]
