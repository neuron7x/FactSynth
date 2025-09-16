"""Validation logic for callback URLs provided by clients."""

from __future__ import annotations

import logging
from collections.abc import Collection
from http import HTTPStatus
from urllib.parse import urlparse

from factsynth_ultimate.core.problem_details import ProblemDetails

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = {"http", "https"}


def _reject(
    url: str,
    *,
    detail: str,
    reason: str,
    title: str = "Invalid callback URL",
    exc: Exception | None = None,
    extras: dict[str, object] | None = None,
) -> ProblemDetails:
    """Return a :class:`ProblemDetails` describing a rejection."""

    if exc is None:
        logger.warning("Rejecting callback URL %s: %s", url, detail)
    else:  # pragma: no cover - defensive, depends on urllib internals
        logger.warning("Rejecting callback URL %s: %s", url, detail, exc_info=exc)

    payload: dict[str, object] = {"reason": reason}
    if extras:
        payload.update(extras)

    return ProblemDetails(
        title=title,
        detail=detail,
        status=int(HTTPStatus.BAD_REQUEST),
        extras=payload,
    )


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
        return _reject(url, detail=detail, reason="invalid_url", exc=exc)

    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        detail = (
            f"Callback URL scheme '{scheme or '[missing]'}' is not allowed. "
            f"Allowed schemes: {', '.join(sorted(ALLOWED_SCHEMES))}."
        )
        return _reject(
            url,
            detail=detail,
            reason="scheme_not_allowed",
            extras={"allowed_schemes": sorted(ALLOWED_SCHEMES)},
        )

    host = (parsed.hostname or "").lower()
    if not host:
        detail = "Callback URL must include a host component"
        return _reject(url, detail=detail, reason="missing_host")

    normalized_allowlist = {item.lower() for item in allowed_hosts if item}
    if not normalized_allowlist:
        detail = "Callback host allowlist is empty"
        return _reject(
            url,
            detail=detail,
            reason="allowlist_empty",
            title="Callback host rejected",
        )

    if host not in normalized_allowlist:
        allowed_preview = sorted(normalized_allowlist)
        detail = (
            f"Callback host '{host}' is not allowed. "
            f"Configured allowlist: {', '.join(allowed_preview)}."
        )
        return _reject(
            url,
            detail=detail,
            reason="host_not_allowed",
            title="Callback host rejected",
            extras={"host": host, "allowed_hosts": allowed_preview},
        )

    return None


__all__ = ["validate_callback_url", "ALLOWED_SCHEMES"]

