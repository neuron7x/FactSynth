"""Core claim evaluation orchestration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from contextlib import ExitStack
from typing import Any

from ..config import ConfigError
from ..core.trace import index, normalize_trace, parse, start_trace
from .redaction import redact_pii
from .retrievers.base import Retriever
from .retrievers.registry import load_configured_retriever, load_retriever

logger = logging.getLogger(__name__)

ResultDict = dict[str, Any]


def evaluate_claim(  # noqa: PLR0913,C901,PLR0912
    claim: str,
    *,
    policy_check: Callable[[str], Any] | None = None,
    scoring: Callable[[str], Any] | None = None,
    diversity: Callable[[str], Any] | None = None,
    nli: Callable[[str], Any] | None = None,
    retriever: Retriever | str | None = None,
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
        Either an instance implementing :class:`Retriever` or the name of a
        registered entry point in the ``factsynth.retrievers`` group. When
        omitted the configured default retriever (if any) will be used.
        Loaded retrievers may optionally define ``close`` or ``aclose`` methods
        which will be invoked when evaluation completes.
    """

    out: ResultDict = {}
    if retriever is None:
        try:
            retriever = load_configured_retriever()
        except ConfigError as exc:
            logger.warning(
                "retriever_config_error",
                extra={"error": str(exc)},
            )
            retriever = None
        except (LookupError, TypeError) as exc:
            logger.warning(
                "retriever_initialisation_failed",
                extra={"error": str(exc)},
            )
            retriever = None
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(
                "retriever_initialisation_failed",
                extra={"error": str(exc)},
            )
            retriever = None
    if isinstance(retriever, str):
        retriever = load_retriever(retriever)
    if retriever is not None:
        if not callable(getattr(retriever, "search", None)):
            raise TypeError("retriever must implement search()")
    with ExitStack() as stack:
        if retriever:
            aclose = getattr(retriever, "aclose", None)
            if callable(aclose):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    stack.callback(lambda: asyncio.run(aclose()))
                else:
                    stack.callback(lambda: loop.create_task(aclose()))
            elif hasattr(retriever, "close"):
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
