"""Shared logging configuration, applied once by each entry point."""

import logging

# One format for every brick, so that collected logs read the same way.
_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    """Send logs to stderr, with the project's common format."""
    logging.basicConfig(level=level, format=_FORMAT)
