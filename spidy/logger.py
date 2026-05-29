"""
spidy/logger.py — Structured logging for Spidy.

Provides debug/info/warn/error logging with optional file output.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime


_LOG: logging.Logger | None = None


def get_logger(name: str = "spidy", log_dir: str | None = None) -> logging.Logger:
    global _LOG
    if _LOG is not None:
        return _LOG

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Console handler (stderr)
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler (if log_dir provided or default)
    if log_dir is None:
        log_dir = str(Path.home() / ".local/share/spidy/logs")
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(
        log_path / f"spidy_{datetime.now().strftime('%Y%m%d')}.log",
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    _LOG = logger
    return logger


def debug(msg: str):
    get_logger().debug(msg)


def info(msg: str):
    get_logger().info(msg)


def warn(msg: str):
    get_logger().warning(msg)


def error(msg: str):
    get_logger().error(msg)
