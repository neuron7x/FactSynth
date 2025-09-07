from __future__ import annotations

import regex as re

from .tokenization import normalize, tokenize

EMOJI_RANGE = (0x1F300, 0x1FAFF)
HEAD_PAT = re.compile(r"^\s*(#+|={3,}|-{3,})", re.M)
LIST_PAT = re.compile(r"^\s*([\-*•·]|\d+\.)\s+", re.M)
SPACE_PAT = re.compile(r"\s+")


def has_emoji(s: str) -> bool:
    """Check if ``s`` contains any emoji characters.

    Args:
        s: Text to inspect.

    Returns:
        True if any character's Unicode code point falls within ``EMOJI_RANGE``,
        otherwise False.

    Edge cases:
        Handles empty strings and only detects emojis whose code points are between
        0x1F300 and 0x1FAFF. Newly introduced emojis outside this range will be
        ignored.
    """
    return any(EMOJI_RANGE[0] <= ord(ch) <= EMOJI_RANGE[1] for ch in s)


def sanitize(
    text: str,
    *,
    forbid_questions: bool = True,
    forbid_headings: bool = True,
    forbid_lists: bool = True,
    forbid_emojis: bool = True,
) -> str:
    """Normalize and scrub free-form text.

    Args:
        text: Raw text that may contain markup or unwanted characters.
        forbid_questions: When True, replaces question marks with periods.
        forbid_headings: When True, strips Markdown-style heading markers.
        forbid_lists: When True, removes common list markers.
        forbid_emojis: When True, drops emoji characters detected by :func:`has_emoji`.

    Returns:
        Cleaned text with collapsed whitespace and no leading or trailing spaces.

    Edge cases:
        - Whitespace is normalized to single spaces and trimmed.
        - Removal of headings or lists may yield an empty string.
        - Only emojis recognized by :func:`has_emoji` are removed; others remain.
    """
    t = normalize(text)
    if forbid_questions:
        t = t.replace("?", ".")
    t = SPACE_PAT.sub(" ", t).strip()
    if forbid_headings and HEAD_PAT.search(t):
        t = HEAD_PAT.sub("", t)
    if forbid_lists and LIST_PAT.search(t):
        t = LIST_PAT.sub("", t)
    if forbid_emojis and has_emoji(t):
        t = re.sub(r"[\p{Emoji_Presentation}]", "", t)
    return t


def ensure_period(text: str) -> str:
    """Ensure that ``text`` ends with a period.

    Args:
        text: Sentence fragment to finalize.

    Returns:
        The text without trailing whitespace and guaranteed to end with ``.``.
        Text already ending with ``.`` or the ellipsis character ``…`` is returned
        unchanged aside from trimming whitespace.

    Edge cases:
        If the input ends with other punctuation (e.g., ``!`` or ``?``), an extra
        period is appended.
    """
    t = text.rstrip()
    return t if t.endswith((".", "…")) else (t + ".")


def fit_length(text: str, target: int) -> str:
    """Return a sentence containing exactly ``target`` words.

    The function trims or pads the input to reach the requested length and ensures
    the result ends with a period.

    Args:
        text: Source text.
        target: Desired number of words; should be a non-negative integer.

    Returns:
        A string with exactly ``target`` tokens, finalized with :func:`ensure_period`.

    Edge cases:
        - When the text is longer than ``target``, filler words (e.g., ``дуже`` or
          ``саме``) are removed before truncating.
        - When shorter, the phrase "Дію послідовно i зважено." is cycled to pad
          the sentence.
        - A ``target`` of zero produces just a period.
    """
    words = tokenize(text)
    if len(words) == target:
        return ensure_period(text)
    if len(words) > target:
        removable = {"дуже", "саме", "реально", "зайве", "надмірно", "дещо", "украй"}
        filtered = [w for w in words if w.lower() not in removable]
        words = filtered if len(filtered) >= target else words
        words = words[:target]
        return ensure_period(" ".join(words))
    pad = ["Дію", "послідовно", "і", "зважено."]  # noqa: RUF001
    i = 0
    while len(words) < target:
        words.append(pad[i % len(pad)])
        i += 1
    return ensure_period(" ".join(words))
