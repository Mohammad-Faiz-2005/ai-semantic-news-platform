"""
Logging configuration for the entire application.

Sets up a consistent log format across all modules.
Usage:
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Something happened")
"""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """
    Configure the root logger with a consistent format.

    Format: timestamp | level | module | message
    Output: stdout (captured by Docker / systemd / etc.)

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        datefmt=date_format,
        force=True,  # Override any existing root logger config
    )

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("faiss").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.

    Args:
        name: Usually __name__ of the calling module

    Returns:
        logging.Logger instance
    """
    return logging.getLogger(name)