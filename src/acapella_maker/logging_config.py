"""Logging configuration for Acapella Maker."""

import logging
import sys
from pathlib import Path
from typing import Optional

# Package logger name
LOGGER_NAME = "acapella_maker"


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module.

    Args:
        name: Module name, typically __name__.

    Returns:
        Logger instance configured under the package logger.
    """
    if name.startswith(LOGGER_NAME):
        return logging.getLogger(name)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    console_output: bool = False,
) -> None:
    """Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to log file.
        console_output: If True, also log to stderr (useful with --verbose).
            Rich console output goes to stdout, so logging to stderr avoids
            interference.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler (if specified)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Console handler (stderr to avoid interfering with Rich on stdout)
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # If no handlers configured, add null handler to avoid warnings
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
