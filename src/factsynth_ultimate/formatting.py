from __future__ import annotations
import regex as re
from .tokenization import tokenize, normalize

EMOJI_RANGE = (0x1F300, 0x1FAFF)
HEAD_PAT = re.compile(r"^\s*(#+|={3,}|-{3,})", re.M)
LIST_PAT = re.compile(r"^\s*([\-*•·]|\d+\.)\s+", re.M)
SPACE_PAT = re.compile(r"\s+")


def has_emoji(s: str) -> bool:
    return any(EMOJI_RANGE[0] <= ord(ch) <= EMOJI_RANGE[1] for ch in s)


def sanitize(
    text: str,
    *,
    forbid_questions=True,
    forbid_headings=True,
    forbid_lists=True,
    forbid_emojis=True,
) -> str:
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
    t = text.rstrip()
    return t if t.endswith((".", "…")) else (t + ".")


def fit_length(text: str, target: int) -> str:
    words = tokenize(text)
    if len(words) == target:
        return ensure_period(text)
    if len(words) > target:
        removable = {
            "дуже",
            "саме",
            "реально",
            "зайве",
            "надмірно",
            "дещо",
            "украй",
        }
        filtered = [w for w in words if w.lower() not in removable]
        words = filtered if len(filtered) >= target else words
        words = words[:target]
        return ensure_period(" ".join(words))
    pad = ["Дію", "послідовно", "і", "зважено."]
    i = 0
    while len(words) < target:
        words.append(pad[i % len(pad)])
        i += 1
    return ensure_period(" ".join(words))
