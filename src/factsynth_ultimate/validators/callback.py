"""Validation logic for callback URLs provided by clients."""

from __future__ import annotations

import logging
from collections.abc import Collection
from http import HTTPStatus
from urllib.parse import urlparse

from factsynth_ultimate.core.problem_details import ProblemDetails

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = {"http", "https"}


def validate_callback_url(url: str, allowed_hosts: Collection[str]) -> ProblemDetails | None:
    """Validate ``url`` against the configured allowlist.

    Args:
        url: Callback URL supplied by the client.
        allowed_hosts: Collection of hostnames permitted for callbacks.

    Returns:
        ``None`` when the URL is acceptable, otherwise a :class:`ProblemDetails`
        instance describing the rejection reason.
    """

    try:
        parsed = urlparse(url)
    except Exception as exc:  # pragma: no cover - defensive guard
        detail = "Callback URL is malformed"
        logger.warning("Rejecting callback URL %s: %s", url, detail, exc_info=exc)
        return ProblemDetails(
            title="Invalid callback URL",
            detail=detail,
            status=int(HTTPStatus.BAD_REQUEST),
        )

    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        detail = (
            f"Callback URL scheme '{scheme or '[missing]'}' is not allowed. "
            f"Allowed schemes: {', '.join(sorted(ALLOWED_SCHEMES))}."
        )
        logger.warning("Rejecting callback URL %s: %s", url, detail)
        return ProblemDetails(
            title="Invalid callback URL",
            detail=detail,
            status=int(HTTPStatus.BAD_REQUEST),
        )

    host = (parsed.hostname or "").lower()
    if not host:
        detail = "Callback URL must include a host component"
        logger.warning("Rejecting callback URL %s: %s", url, detail)
        return ProblemDetails(
            title="Invalid callback URL",
            detail=detail,
            status=int(HTTPStatus.BAD_REQUEST),
        )

    normalized_allowlist = {item.lower() for item in allowed_hosts if item}
    if not normalized_allowlist:
        detail = "Callback host allowlist is empty"
        logger.warning("Rejecting callback URL %s: %s", url, detail)
        return ProblemDetails(
            title="Callback host rejected",
            detail=detail,
            status=int(HTTPStatus.BAD_REQUEST),
        )

    if host not in normalized_allowlist:
        allowed_preview = ", ".join(sorted(normalized_allowlist))
        detail = (
            f"Callback host '{host}' is not allowed. "
            f"Configured allowlist: {allowed_preview}."
        )
        logger.warning("Rejecting callback URL %s: %s", url, detail)
        return ProblemDetails(
            title="Callback host rejected",
            detail=detail,
            status=int(HTTPStatus.BAD_REQUEST),
        )

    return None


__all__ = ["validate_callback_url", "ALLOWED_SCHEMES"]
