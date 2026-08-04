"""
Enterprise logging configuration for AGCT.

Features
--------
- Structured logging with structlog
- Console logging
- Rotating file logging
- Separate application and error logs
- UTC timestamps
- Thread-safe
"""

from __future__ import annotations

import logging
import logging.config
from logging.handlers import RotatingFileHandler
from pathlib import Path

import structlog

from app.core.config import settings

# ----------------------------------------------------------
# Log Directory
# ----------------------------------------------------------

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

APP_LOG = LOG_DIR / "agct.log"
ERROR_LOG = LOG_DIR / "error.log"


def configure_logging() -> None:
    """
    Configure Python logging and structlog.

    This function should be called once during application startup.
    """

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": (
                        "%(asctime)s | "
                        "%(levelname)s | "
                        "%(name)s | "
                        "%(message)s"
                    )
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": settings.LOG_LEVEL,
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "standard",
                    "filename": str(APP_LOG),
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 5,
                    "encoding": "utf-8",
                    "level": settings.LOG_LEVEL,
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "standard",
                    "filename": str(ERROR_LOG),
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 5,
                    "encoding": "utf-8",
                    "level": "ERROR",
                },
            },
            "root": {
                "handlers": [
                    "console",
                    "file",
                    "error_file",
                ],
                "level": settings.LOG_LEVEL,
            },
        }
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.INFO
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """
    Returns a configured logger instance.

    Example
    -------
    logger = get_logger(__name__)
    """

    return structlog.get_logger(name)