r"""Utilities for Unicode-aware tokenization.

The module exposes a small set of helpers to break text into word and number
tokens.  All input is first normalised to Unicode NFC form so that characters
with combining marks are represented consistently.  Tokenisation is performed
using a single regular expression, ``_TOKEN_RE``:

``r"[\p{L}\p{N}\u02BC'\-]+"``

The pattern matches runs of Unicode letters (``\p{L}``) or digits (``\p{N}``)
and allows embedded apostrophes (both the ASCII ``'`` and the Ukrainian
``\u02BC``) as well as hyphens.  Any other punctuation or whitespace acts as a
separator.
Because the pattern relies on Unicode categories, text containing multiple
languages is handled naturally; for example, ``"Hola мир 42"`` tokenises to
``["Hola", "мир", "42"]``.
"""

import unicodedata

import regex as re

_TOKEN_RE = re.compile(r"[\p{L}\p{N}\u02BC'\-]+", re.UNICODE)


def normalize(text: str) -> str:
    """Return *text* normalised to Unicode NFC form.

    Canonical composition via :func:`unicodedata.normalize` ensures that
    equivalent character sequences across different languages use the same
    binary representation.  This is important when processing mixed-language
    text where combining marks might otherwise produce distinct tokens.
    """

    return unicodedata.normalize("NFC", text)


def tokenize(text: str) -> list[str]:
    """Split *text* into a list of tokens.

    The input is first passed through :func:`normalize` and then matched against
    ``_TOKEN_RE``.  Tokens consist of consecutive letters or digits and may
    include internal apostrophes or hyphens.  Punctuation other than these
    characters acts as a delimiter.  Because the regular expression operates on
    Unicode properties, tokens are produced correctly for mixed-language input
    such as ``"naïve 世界 123"``.
    """

    return _TOKEN_RE.findall(normalize(text))


def count_words(text: str) -> int:
    """Return the number of tokens found in *text*.

    This simply counts the results of :func:`tokenize`, so numbers and words
    separated by punctuation are all considered individual tokens.
    """

    return len(tokenize(text))

