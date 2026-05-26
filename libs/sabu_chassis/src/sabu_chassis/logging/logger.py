from __future__ import annotations

import logging


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger that works with sabu-chassis logging configuration.

    Libraries should use this helper instead of calling configure_logging().
    The application or workflow entry point remains responsible for configuring
    handlers, levels, formatting, and file destinations.
    """
    logger = logging.getLogger(name)
    has_null_handler = any(
        isinstance(handler, logging.NullHandler)
        for handler in logger.handlers
    )
    if not has_null_handler:
        logger.addHandler(logging.NullHandler())
    return logger
