"""Core claim evaluation orchestration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import ExitStack
from typing import Any

from ..core.trace import index, normalize_trace, parse, start_trace
from .redaction import redact_pii

logger = logging.getLogger(__name__)

ResultDict = dict[str, Any]


def evaluate_claim(  # noqa: PLR0913
    claim: str,
    *,
    policy_check: Callable[[str], Any] | None = None,
    scoring: Callable[[str], Any] | None = None,
    diversity: Callable[[str], Any] | None = None,
    nli: Callable[[str], Any] | None = None,
    retriever: Any | None = None,
) -> ResultDict:
    """Evaluate *claim* and compose results from several subsystems.

    Parameters
    ----------
    claim:
        The textual claim to analyse.
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

        evidence: list[dict[str, Any]] = []
        if retriever and hasattr(retriever, "search"):
            try:
                docs = retriever.search(claim)
            except Exception as exc:
                logger.exception(
                    "retriever_search_error",
                    extra={"claim": claim, "error": str(exc)},
                )
                docs = []
            for doc in docs:
                url = getattr(doc, "id", "")
                content = getattr(doc, "text", "")
                content = redact_pii(content)
                trace = start_trace(url, content)
                trace = parse(trace)
                trace = normalize_trace(trace)
                trace = index(trace)
                evidence.append(
                    {
                        "source_id": trace.source_id,
                        "source": url,
                        "content": trace.content,
                    }
                )
        out["evidence"] = evidence

        if policy_check is not None:
            out["policy"] = policy_check(claim)
        if scoring is not None:
            out["score"] = scoring(claim)
        if diversity is not None:
            out["diversity"] = diversity(claim)
        if nli is not None:
            out["nli"] = nli(claim)

    return out
