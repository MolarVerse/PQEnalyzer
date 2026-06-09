import logging

from PQEnalyzer._logging import (RESET_COLOR, RuntimeFormatter,
                                 PACKAGE_LOGGER_NAME, configure_logging,
                                 get_logger)


class FakeStream:

    def __init__(self, is_tty):
        self.is_tty = is_tty

    def flush(self):
        return None

    def isatty(self):
        return self.is_tty

    def write(self, message):
        return len(message)


def test_get_logger_returns_package_logger_names():
    assert get_logger().name == PACKAGE_LOGGER_NAME
    assert get_logger("").name == PACKAGE_LOGGER_NAME
    assert get_logger(PACKAGE_LOGGER_NAME).name == PACKAGE_LOGGER_NAME
    assert get_logger("plots").name == "PQEnalyzer.plots"
    assert get_logger("PQEnalyzer.apps.app").name == "PQEnalyzer.apps.app"


def make_record(level, message):
    return logging.LogRecord(
        name="PQEnalyzer.tests",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )


def test_runtime_formatter_colorizes_by_level():
    formatter = RuntimeFormatter(use_color=True)

    message = formatter.format(make_record(logging.WARNING, "Careful"))

    assert message == f"\033[33mWARNING: Careful{RESET_COLOR}"


def test_runtime_formatter_can_disable_color():
    formatter = RuntimeFormatter(use_color=False)

    message = formatter.format(make_record(logging.ERROR, "Failed"))

    assert message == "ERROR: Failed"


def test_configure_logging_delegates_to_standard_logging(monkeypatch):
    calls = []
    fake_stream = FakeStream(is_tty=True)

    monkeypatch.setattr(logging, "basicConfig",
                        lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr("sys.stderr", fake_stream)
    monkeypatch.delenv("NO_COLOR", raising=False)

    configure_logging(logging.DEBUG)

    handler = calls[0]["handlers"][0]

    assert calls[0]["level"] == logging.DEBUG
    assert handler.stream is fake_stream
    assert handler.formatter.format(make_record(
        logging.ERROR, "Failed")) == f"\033[31mERROR: Failed{RESET_COLOR}"


def test_configure_logging_respects_no_color(monkeypatch):
    calls = []
    fake_stream = FakeStream(is_tty=True)

    monkeypatch.setattr(logging, "basicConfig",
                        lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr("sys.stderr", fake_stream)
    monkeypatch.setenv("NO_COLOR", "1")

    configure_logging()

    handler = calls[0]["handlers"][0]

    assert handler.formatter.format(make_record(logging.ERROR,
                                                "Failed")) == "ERROR: Failed"
