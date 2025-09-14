"""Common logging setup used across the service."""

from __future__ import annotations

import logging
import os

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
