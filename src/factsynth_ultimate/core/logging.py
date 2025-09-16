"""Common logging setup used across the service."""

from __future__ import annotations

import logging
import os
from contextlib import suppress

from pythonjsonlogger import jsonlogger

from .request_id import get_request_id


class RequestIdFilter(logging.Filter):
    """Attach the current request ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - trivial
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id() or ""
        return True


def setup_logging() -> None:
    """Initialise the root logger from environment settings."""

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler()
    handler.setFormatter(jsonlogger.JsonFormatter())
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    audit_logger = logging.getLogger("factsynth.audit")
    for existing in list(audit_logger.handlers):
        audit_logger.removeHandler(existing)
        with suppress(Exception):
            existing.close()
    audit_handler = logging.FileHandler("audit.log", encoding="utf-8")
    audit_handler.setFormatter(jsonlogger.JsonFormatter())
    audit_handler.addFilter(RequestIdFilter())
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(level)
    audit_logger.propagate = False
