"""Lightweight text normalisation and tokenization helpers."""

from __future__ import annotations

import unicodedata
from typing import List

import regex as re

# Matches runs of Unicode word characters (letters, marks, digits, underscore).
_WORD_RE = re.compile(r"\w+", flags=re.UNICODE)
# Collapses any whitespace sequence into a single space.
_SPACE_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Return a Unicode-normalized, whitespace-collapsed string.

    The function applies NFC/KC normalization, replaces non-breaking spaces with
    regular spaces and collapses consecutive whitespace into a single space.
    Leading and trailing whitespace is stripped from the result.
    """
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    t = t.replace("\u00a0", " ")
    t = _SPACE_RE.sub(" ", t)
    return t.strip()


def tokenize(text: str) -> List[str]:
    """Split ``text`` into individual word tokens.

    The input is first :func:`normalize`d. Tokens are defined as runs of Unicode
    word characters (letters, digits or underscore). The returned list preserves
    the original order of tokens.
    """
    norm = normalize(text)
    return _WORD_RE.findall(norm)
