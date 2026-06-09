"""
Logging helpers for PQEnalyzer runtime messages.
"""

import logging
import os
import sys


PACKAGE_LOGGER_NAME = "PQEnalyzer"
RESET_COLOR = "\033[0m"
LEVEL_COLORS = {
    logging.DEBUG: "\033[2m",
    logging.INFO: "\033[34m",
    logging.WARNING: "\033[33m",
    logging.ERROR: "\033[31m",
    logging.CRITICAL: "\033[1;31m",
}


class RuntimeFormatter(logging.Formatter):
    """
    Format user-facing runtime messages with optional ANSI colors.
    """

    def __init__(self, use_color=False):
        super().__init__("%(levelname)s: %(message)s")
        self.use_color = use_color

    def format(self, record):
        message = super().format(record)

        if not self.use_color:
            return message

        color = LEVEL_COLORS.get(record.levelno)
        return f"{color}{message}{RESET_COLOR}" if color else message


def get_logger(name=None):
    """
    Return a package logger for the given module or component name.
    """
    if name in {None, "", PACKAGE_LOGGER_NAME}:
        return logging.getLogger(PACKAGE_LOGGER_NAME)

    if name.startswith(f"{PACKAGE_LOGGER_NAME}."):
        return logging.getLogger(name)

    return logging.getLogger(f"{PACKAGE_LOGGER_NAME}.{name}")


def configure_logging(level=logging.INFO):
    """
    Configure user-facing CLI logging if the application has no handlers yet.
    """
    stream = sys.stderr
    use_color = _should_use_color(stream)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(RuntimeFormatter(use_color=use_color))

    logging.basicConfig(level=level, handlers=[handler])


def _should_use_color(stream):
    """
    Return whether ANSI colors should be emitted for the given stream.
    """
    return ("NO_COLOR" not in os.environ and hasattr(stream, "isatty")
            and stream.isatty())
