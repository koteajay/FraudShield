"""Structured logging configuration for FraudShield."""

import logging
import sys
from app.config import get_settings


def setup_logging() -> logging.Logger:
    """Configures Python's standard logging library with structured formatting."""
    settings = get_settings()

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Suppress overly chatty external loggers
    logging.getLogger("uvicorn.access").setLevel(log_level)

    logger = logging.getLogger("fraudshield")
    logger.setLevel(log_level)
    return logger


logger = logging.getLogger("fraudshield")
