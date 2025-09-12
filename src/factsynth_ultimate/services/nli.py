"""Natural language inference support utilities."""

from __future__ import annotations

from typing import Awaitable, Callable, Optional

from ..tokenization import tokenize

Classifier = Callable[[str, str], Awaitable[float]]


class NLI:
    """Natural language inference with optional async classifier."""

    def __init__(self, classifier: Optional[Classifier] = None) -> None:
        self.classifier = classifier

    async def classify(self, premise: str, hypothesis: str) -> float:
        """Return entailment score for *hypothesis* given *premise*.

        If an async *classifier* was provided, it will be awaited. Any exception
        raised by the classifier triggers a heuristic fallback based on token
        overlap.
        """

        if self.classifier is not None:
            try:
                return await self.classifier(premise, hypothesis)
            except Exception:  # noqa: BLE001
                pass
        return self._heuristic(premise, hypothesis)

    def _heuristic(self, premise: str, hypothesis: str) -> float:
        p_tokens = {t.lower() for t in tokenize(premise)}
        h_tokens = {t.lower() for t in tokenize(hypothesis)}
        if not h_tokens:
            return 0.0
        return len(h_tokens & p_tokens) / len(h_tokens)
