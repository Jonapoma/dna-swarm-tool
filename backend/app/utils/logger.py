"""Logging setup for GenomicSwarm backend."""

import logging
import os
import sys

_loggers = {}


def setup_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    _loggers[name] = logger
    return logger


def get_logger(name: str) -> logging.Logger:
    if name not in _loggers:
        return setup_logger(name)
    return _loggers[name]
