"""Logging configuration helpers for sensor_toolkit."""

import logging
import sys
from pathlib import Path


def setup_logging(
    level: int = logging.DEBUG,
    log_file: Path | None = Path("sensor_toolkit.log"),
    fmt: str = "%(asctime)s %(levelname)-8s %(name)s - %(message)s",
) -> None:
    """Configure sensor_toolkit logging to write to a file and the console.

    Attaches handlers to the ``sensor_toolkit`` package logger. Call this once
    at your application entry point before using any toolkit functions.

    Args:
        level: Logging level applied to all handlers (default: ``logging.DEBUG``).
        log_file: Path to the log file. Pass ``None`` to disable file logging.
        fmt: Log record format string (default includes timestamp, level, logger name).

    Examples:
        >>> from pathlib import Path
        >>> from sensor_toolkit.logging_config import setup_logging
        >>> setup_logging(log_file=Path("my_run.log"))

        Disable file output (console only):

        >>> setup_logging(log_file=None)
    """
    pkg_logger = logging.getLogger("sensor_toolkit")
    pkg_logger.setLevel(level)

    # Avoid adding duplicate handlers if called more than once.
    pkg_logger.handlers.clear()

    formatter = logging.Formatter(fmt)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    pkg_logger.addHandler(console_handler)

    if log_file is not None:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        pkg_logger.addHandler(file_handler)
