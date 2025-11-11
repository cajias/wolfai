"""Logging management for WolfAI."""

import logging
import sys


def configure_basic_logging(
    level: int = logging.DEBUG, name: str | None = None,
) -> logging.Logger:
    """Configure basic logging with standard format.

    Args:
        level: Logging level (default: DEBUG)
        name: Logger name to return (default: __name__ from caller)

    Returns:
        Logger instance
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    return logging.getLogger(name or __name__)


__all__ = ["configure_basic_logging"]
