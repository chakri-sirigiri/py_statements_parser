"""Logging configuration for Py Statements Parser."""

import sys
from pathlib import Path

from loguru import logger


def setup_logging(verbose: bool = False, log_file: str = None) -> None:
    """Setup logging configuration with log4j style formatting."""

    # Remove default logger
    logger.remove()

    # Determine log level
    log_level = "DEBUG" if verbose else "INFO"

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Set default log file path if not provided
    if log_file is None:
        log_file = logs_dir / "app.log"

    # Console handler with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # File handler with rotation - logs will be archived to logs/ folder
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    # Add correlation ID and service context
    logger.configure(
        extra={
            "service": "py-statements-parser",
            "environment": "development",
        }
    )


def get_logger(name: str = None):
    """Get a logger instance with the specified name."""
    return logger.bind(name=name or __name__)
