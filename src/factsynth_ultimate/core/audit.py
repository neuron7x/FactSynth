from __future__ import annotations
import logging

log = logging.getLogger("factsynth.audit")

def audit_event(action: str, subject: str) -> None:
    try:
        log.info("%s %s", action, subject)
    except Exception:
        pass
