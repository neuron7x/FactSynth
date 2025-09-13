"""Core claim evaluation orchestration."""

from __future__ import annotations

from contextlib import ExitStack
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, Optional, Tuple

ResultDict = Dict[str, Any]


def evaluate_claim(  # noqa: PLR0913
    claim: str,
    *,
    region: str | None = None,
    language: str | None = None,
    time_range: Tuple[datetime, datetime] | None = None,
    policy_check: Callable[[str], Any] | None = None,
    scoring: Callable[[str], Any] | None = None,
    diversity: Callable[[str], Any] | None = None,
    nli: Callable[[str], Any] | None = None,
    retriever: Optional[Any] = None,
) -> ResultDict:
    """Evaluate *claim* and compose results from several subsystems.

    Parameters
    ----------
    claim:
        The textual claim to analyse.
    region, language, time_range:
        Optional domain context. Currently unused but accepted for forward
        compatibility with enriched evaluators.
    policy_check, scoring, diversity, nli:
        Optional callables implementing each stage. They are invoked with the
        claim and their results are merged into the output dictionary under
        corresponding keys. Missing callables simply yield ``None``.
    retriever:
        Optional object providing ``search`` and, optionally, ``close`` methods.
        If a ``close`` method is present it will be invoked once the evaluation
        is complete.
    """

    out: ResultDict = {}
    with ExitStack() as stack:
        if retriever and hasattr(retriever, "close"):
            stack.callback(retriever.close)

        evidence: Iterable[Any] = []
        if retriever and hasattr(retriever, "search"):
            try:
                evidence = retriever.search(claim)
            except Exception:  # noqa: BLE001 - defensive best effort
                evidence = []
        out["evidence"] = list(evidence)

        if policy_check is not None:
            out["policy"] = policy_check(claim)
        if scoring is not None:
            out["score"] = scoring(claim)
        if diversity is not None:
            out["diversity"] = diversity(claim)
        if nli is not None:
            out["nli"] = nli(claim)

    return out
