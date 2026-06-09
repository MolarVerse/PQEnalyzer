import customtkinter as ctk
import matplotlib.pyplot as plt
import pytest

from PQEnalyzer.apps import app as app_module


class FakeFlag:

    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class FakeEntry:

    def __init__(self, value=""):
        self.value = value
        self.state = None

    def configure(self, state):
        self.state = state

    def delete(self, start, end):
        self.value = ""

    def insert(self, index, value):
        self.value = value + self.value

    def get(self):
        return self.value


class DummyPlot:
    instances = []

    def __init__(self, app):
        self.app = app
        self.calls = []
        self.instances.append(self)

    def follow(self, info_parameter, interval):
        self.calls.append(("follow", info_parameter, interval))

    def simple(self, info_parameter):
        self.calls.append(("simple", info_parameter))


@pytest.fixture(autouse=True)
def reset_dummy_plots():
    DummyPlot.instances = []


def make_app(follow=False, interval=""):
    app = object.__new__(app_module.App)
    app.follow = FakeFlag(follow)
    app.interval = FakeEntry(interval)
    app.list_of_plots = []
    app._App__selected_info = "TEMPERATURE"
    return app


def test_apps_package_does_not_import_gui_module_for_terminal_app():
    import importlib
    import sys

    sys.modules.pop("PQEnalyzer.apps", None)
    sys.modules.pop("PQEnalyzer.apps.app", None)

    apps = importlib.import_module("PQEnalyzer.apps")

    assert apps.TermApp.__name__ == "TermApp"
    assert "PQEnalyzer.apps.app" not in sys.modules


@pytest.mark.parametrize(
    "value, expected",
    [
        ("", True),
        (".", True),
        ("1", True),
        ("1.5", True),
        ("0", True),
        ("abc", False),
        ("1.2.3", False),
        ("-1", False),
    ],
)
def test_validate_number(value, expected):
    assert app_module.App.validate_number(None, value) is expected


def test_parse_positive_float_uses_default_for_empty_entry():
    assert app_module.App.parse_positive_float(None, "", 1.0,
                                               "Interval") == 1.0
    assert app_module.App.parse_positive_float(None, ".", 1.0,
                                               "Interval") == 1.0


def test_parse_positive_float_rejects_non_positive_values():
    with pytest.raises(ValueError, match="Interval must be greater than zero"):
        app_module.App.parse_positive_float(None, "0", 1.0, "Interval")


def test_toggle_entry_state_resets_entry_before_insert():
    entry = FakeEntry("previous")

    app_module.App.toggle_entry_state(None, FakeFlag(True), entry, "1.0")

    assert entry.state == "normal"
    assert entry.value == "1.0"


def test_toggle_entry_state_clears_entry_when_disabled():
    entry = FakeEntry("previous")

    app_module.App.toggle_entry_state(None, FakeFlag(False), entry, "1.0")

    assert entry.state == "disabled"
    assert entry.value == ""


def test_destroy_closes_plots_and_tk_window(monkeypatch):
    calls = []

    monkeypatch.setattr(plt, "close", lambda target: calls.append(
        ("close", target)))
    monkeypatch.setattr(app_module.App, "quit",
                        lambda self: calls.append(("quit", None)))
    monkeypatch.setattr(ctk.CTk, "destroy",
                        lambda self: calls.append(("destroy", None)))

    app_module.App.destroy(object.__new__(app_module.App))

    assert calls == [("close", "all"), ("quit", None), ("destroy", None)]


def test_plot_button_rejects_invalid_follow_interval(monkeypatch, caplog):
    app = make_app(follow=True, interval="0")
    monkeypatch.setattr(app_module, "PlotTime", DummyPlot)

    app_module.App._App__plot_button_event(app, 0)

    assert app.list_of_plots == []
    assert DummyPlot.instances == []
    assert "Interval must be greater than zero" in caplog.text


def test_plot_button_passes_valid_follow_interval(monkeypatch):
    app = make_app(follow=True, interval="2.5")
    monkeypatch.setattr(app_module, "PlotTime", DummyPlot)

    app_module.App._App__plot_button_event(app, 0)

    assert app.list_of_plots == DummyPlot.instances
    assert DummyPlot.instances[0].calls == [("follow", "TEMPERATURE", 2.5)]


def test_plot_button_runs_simple_histogram(monkeypatch):
    app = make_app(follow=False)
    monkeypatch.setattr(app_module, "PlotHistogram", DummyPlot)

    app_module.App._App__plot_button_event(app, 1)

    assert app.list_of_plots == DummyPlot.instances
    assert DummyPlot.instances[0].calls == [("simple", "TEMPERATURE")]


def test_plot_button_rejects_unknown_event():
    with pytest.raises(ValueError, match="Unknown plot event"):
        app_module.App._App__plot_button_event(make_app(), 3)
