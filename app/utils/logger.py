"""
logger.py
---------
Provides a shared logger factory for all ToolPilot modules.
Each module gets a named logger that writes formatted output to stdout.
"""
import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger with the given name.
    Avoids duplicate handlers if called multiple times with the same name.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%H:%M:%S"
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
