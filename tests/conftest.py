import logging

import matplotlib
import pytest


matplotlib.use("Agg")


@pytest.fixture(name="terminal_log")
def terminal_log_fixture(caplog):
    """Capture records from the independent application event logger."""
    from PQEnalyzer._terminal import event_logger

    previous_level = event_logger.level
    event_logger.setLevel(logging.DEBUG)
    event_logger.addHandler(caplog.handler)
    caplog.clear()
    try:
        yield caplog
    finally:
        event_logger.removeHandler(caplog.handler)
        event_logger.setLevel(previous_level)
