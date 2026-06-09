"""
Logging helpers for PQEnalyzer runtime messages.
"""

import logging


PACKAGE_LOGGER_NAME = "PQEnalyzer"


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
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
