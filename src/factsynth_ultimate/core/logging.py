"""Common logging setup used across the service."""

from __future__ import annotations

import logging
import os


def setup_logging() -> None:
    """Initialise the root logger from environment settings."""

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
