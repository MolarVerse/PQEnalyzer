import logging

from PQEnalyzer._logging import (PACKAGE_LOGGER_NAME, configure_logging,
                                 get_logger)


def test_get_logger_returns_package_logger_names():
    assert get_logger().name == PACKAGE_LOGGER_NAME
    assert get_logger("").name == PACKAGE_LOGGER_NAME
    assert get_logger(PACKAGE_LOGGER_NAME).name == PACKAGE_LOGGER_NAME
    assert get_logger("plots").name == "PQEnalyzer.plots"
    assert get_logger("PQEnalyzer.apps.app").name == "PQEnalyzer.apps.app"


def test_configure_logging_delegates_to_standard_logging(monkeypatch):
    calls = []

    monkeypatch.setattr(logging, "basicConfig",
                        lambda **kwargs: calls.append(kwargs))

    configure_logging(logging.DEBUG)

    assert calls == [{
        "level": logging.DEBUG,
        "format": "%(levelname)s: %(message)s",
    }]
