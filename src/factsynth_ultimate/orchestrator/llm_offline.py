from typing import Optional
import random


class OfflineLLM:
    """Детермінований офлайн-генератор: стилізована трансформація, без мережі."""

    def __init__(self, seed: int = 7):
        random.seed(seed)

    def generate(
        self, prompt: str, system: Optional[str] = None, temperature: float = 0.2
    ) -> str:
        lines = [line.strip() for line in prompt.splitlines() if line.strip()]
        head = lines[:2]
        body = " ".join(lines[2:])[:1200]
        tags = ", ".join(
            sorted(set([w.lower() for w in body.split() if len(w) > 7]))[:6]
        )
        return f"{' '.join(head)}\n\n{body}\n\n[offline-synth • temp={temperature} • tags: {tags}]"
