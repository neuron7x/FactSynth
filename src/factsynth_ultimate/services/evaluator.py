"""Core claim evaluation orchestration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from contextlib import ExitStack
from typing import Any

from ..core.trace import index, normalize_trace, parse, start_trace
from ..core.tracing import trace
from .redaction import redact_pii

logger = logging.getLogger(__name__)

ResultDict = dict[str, Any]


def evaluate_claim(  # noqa: PLR0913,C901
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
        Optional object providing ``search`` and, optionally, ``close`` or
        ``aclose`` methods. If an ``aclose`` coroutine is present it will be
        executed via :func:`asyncio.run`; otherwise any ``close`` method will
        be invoked once the evaluation is complete.
    """

    tracer = trace.get_tracer(__name__)

    out: ResultDict = {}
    with ExitStack() as stack:
        if retriever:
            if hasattr(retriever, "aclose"):
                stack.callback(lambda: asyncio.run(retriever.aclose()))
            elif hasattr(retriever, "close"):
                stack.callback(retriever.close)

        evidence: list[dict[str, Any]] = []
        if retriever and hasattr(retriever, "search"):
            with tracer.start_as_current_span("retriever.search", attributes={"claim": claim}):
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
                with tracer.start_as_current_span("retriever.process_doc", attributes={"source": url}):
                    content = getattr(doc, "text", "")
                    content = redact_pii(content)
                    trace_obj = start_trace(url, content)
                    trace_obj = parse(trace_obj)
                    trace_obj = normalize_trace(trace_obj)
                    trace_obj = index(trace_obj)
                    evidence.append(
                        {
                            "source_id": trace_obj.source_id,
                            "source": url,
                            "content": trace_obj.content,
                        }
                    )
        out["evidence"] = evidence

        if policy_check is not None:
            with tracer.start_as_current_span("policy_check"):
                out["policy"] = policy_check(claim)
        if scoring is not None:
            with tracer.start_as_current_span("scoring"):
                out["score"] = scoring(claim)
        if diversity is not None:
            with tracer.start_as_current_span("diversity"):
                out["diversity"] = diversity(claim)
        if nli is not None:
            with tracer.start_as_current_span("nli"):
                out["nli"] = nli(claim)

    return out
