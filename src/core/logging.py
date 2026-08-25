"""Centralized structured logging infrastructure using Loguru."""

import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger


class InterceptHandler(logging.Handler):
    """Intercepts standard library logging records and redirects them to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
) -> None:
    """Configures application-wide logging handlers and formats."""
    # Remove existing default Loguru handlers
    logger.remove()

    # Standard console format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Add console sink
    logger.add(
        sys.stdout,
        level=log_level.upper(),
        format=log_format,
        colorize=True,
        enqueue=True,
    )

    # Optional file sink
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_file),
            level=log_level.upper(),
            format=log_format,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            enqueue=True,
        )

    # Redirect standard library logging (e.g. from CrewAI, ChromaDB, HTTPX, Uvicorn)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Suppress overly noisy 3rd-party loggers
    for noisy_logger in ["httpcore", "httpx", "chromadb", "urllib3"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


# Default initialization
setup_logging()
