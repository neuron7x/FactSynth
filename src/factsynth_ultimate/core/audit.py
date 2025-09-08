from __future__ import annotations

import logging
from contextlib import suppress

log = logging.getLogger("factsynth.audit")


def audit_event(action: str, subject: str) -> None:
    """Log audit events, ignoring logging failures."""
    with suppress(Exception):
        log.info("%s %s", action, subject)
