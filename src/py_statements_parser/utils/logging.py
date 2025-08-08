"""Logging configuration for Py Statements Parser."""

import sys
from pathlib import Path
from loguru import logger


def setup_logging(verbose: bool = False, log_file: str = "app.log") -> None:
    """Setup logging configuration with log4j style formatting."""
    
    # Remove default logger
    logger.remove()
    
    # Determine log level
    log_level = "DEBUG" if verbose else "INFO"
    
    # Console handler with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        level=log_level,
        colorize=True,
    )
    
    # File handler with rotation
    logger.add(
        log_file,
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