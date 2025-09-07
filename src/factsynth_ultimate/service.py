from __future__ import annotations


def synthesize(prompt: str, max_tokens: int = 128) -> str:
    tokens = [t for t in prompt.strip().split() if t]
    trunc = tokens[: max(1, max_tokens)]
    text = " ".join(trunc)
    checksum = sum(ord(c) for c in text) % 997
    return f"{text} |ck:{checksum:03d}"
