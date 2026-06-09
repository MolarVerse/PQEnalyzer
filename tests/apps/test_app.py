from types import SimpleNamespace

import customtkinter as ctk
import matplotlib.pyplot as plt
import pytest

from PQEnalyzer.apps import app as app_module
from PQEnalyzer.apps import app_layout
from PQEnalyzer.apps import termapp as termapp_module


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


class FakeWidget:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.grid_calls = []
        self.configured_rows = []
        self.configured_columns = []

    def grid(self, *args, **kwargs):
        self.grid_calls.append((args, kwargs))

    def grid_rowconfigure(self, *args, **kwargs):
        self.configured_rows.append((args, kwargs))

    def grid_columnconfigure(self, *args, **kwargs):
        self.configured_columns.append((args, kwargs))

    def set(self, value):
        self.value = value

    def configure(self, *args, **kwargs):
        self.configure_args = args
        self.configure_kwargs = kwargs


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


def test_build_creates_gui_view_classes(monkeypatch):
    app = object.__new__(app_module.App)
    calls = []

    def view_factory(name):

        class FakeView:

            def __init__(self, *args):
                self.args = args
                calls.append((name, self, args))

        return FakeView

    monkeypatch.setattr(app_module, "SidebarView", view_factory("sidebar"))
    monkeypatch.setattr(app_module, "PlotControlsView",
                        view_factory("plot"))
    monkeypatch.setattr(app_module, "ParameterSelectorView",
                        view_factory("parameter"))
    monkeypatch.setattr(app_module, "StatisticsControlsView",
                        view_factory("statistics"))

    app_module.App.build(app)

    assert [call[0] for call in calls] == [
        "sidebar",
        "plot",
        "parameter",
        "statistics",
    ]
    assert app.sidebar_view is calls[0][1]
    assert app.plot_controls_view is calls[1][1]
    assert app.parameter_selector_view is calls[2][1]
    assert app.statistics_controls_view is calls[3][1]
    assert all(call[2][0] is app for call in calls)
    assert all(len(call[2]) > 1 for call in calls[:3])


def test_parameter_selector_view_sets_initial_selection(monkeypatch):
    app = SimpleNamespace(info=["TEMPERATURE", "PRESSURE"])
    selected = []

    monkeypatch.setattr(app_layout.ctk, "CTkFrame", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkLabel", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkOptionMenu", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkFont",
                        lambda *args, **kwargs: ("font", args, kwargs))

    view = app_layout.ParameterSelectorView(app, selected.append)

    assert selected == ["TEMPERATURE"]
    assert app.info_frame is view.frame
    assert app.info_label is view.label
    assert app.info_optionmenu is view.optionmenu
    assert app.info_optionmenu.kwargs["values"] == ["TEMPERATURE", "PRESSURE"]
    assert app.info_optionmenu.kwargs["command"] == selected.append


def test_statistics_controls_view_exposes_plot_state_attributes(monkeypatch):
    app = SimpleNamespace(
        register=lambda callback: callback,
        validate_number=lambda value: True,
        toggle_entry_state=lambda event, entry, default="": None,
    )

    monkeypatch.setattr(app_layout.ctk, "CTkFrame", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkLabel", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkCheckBox", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkEntry", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkFont",
                        lambda *args, **kwargs: ("font", args, kwargs))

    view = app_layout.StatisticsControlsView(app)

    assert app.settings_frame is view.frame
    assert app.statistics_frame is view.statistics_frame
    assert app.time_series_frame is view.time_series_frame
    assert app.mean is view.mean
    assert app.median is view.median
    assert app.cummulative_average is view.cumulative_average
    assert app.self_correlation_mean is view.self_correlation_mean
    assert app.difference is view.difference
    assert app.running_average is view.running_average
    assert app.window_size is view.window_size
    assert view.mean.args[0] is view.statistics_frame
    assert view.median.args[0] is view.statistics_frame
    assert view.cumulative_average.args[0] is view.time_series_frame
    assert view.self_correlation_mean.args[0] is view.time_series_frame
    assert view.difference.args[0] is view.time_series_frame
    assert view.running_average.args[0] is view.time_series_frame
    assert view.window_size.args[0] is view.time_series_frame


def test_difference_checkbox_enables_no_data(monkeypatch):
    class FakeBoolean:

        def __init__(self):
            self.value = False

        def set(self, value):
            self.value = value

    app = SimpleNamespace(
        register=lambda callback: callback,
        validate_number=lambda value: True,
        toggle_entry_state=lambda event, entry, default="": None,
        plot_main_data=FakeBoolean(),
    )

    monkeypatch.setattr(app_layout.ctk, "CTkFrame", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkLabel", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkCheckBox", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkEntry", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkFont",
                        lambda *args, **kwargs: ("font", args, kwargs))

    view = app_layout.StatisticsControlsView(app)
    view.difference.get = lambda: True

    view.difference.kwargs["command"]()

    assert app.plot_main_data.value is True


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


def test_change_appearance_mode_updates_matplotlib_and_open_plots(monkeypatch):
    app = make_app()
    calls = []

    class FakeFigure:

        def __init__(self, number):
            self.number = number

    class FakePlot:

        def __init__(self, number):
            self.figure = FakeFigure(number)

        def redraw(self):
            calls.append(("redraw", self.figure.number))

    open_plot = FakePlot(1)
    closed_plot = FakePlot(2)
    app.list_of_plots = [open_plot, closed_plot]

    monkeypatch.setattr(app_module.ctk, "set_appearance_mode",
                        lambda mode: calls.append(("ctk", mode)))
    monkeypatch.setattr(app_module, "resolve_appearance_mode",
                        lambda mode: "Dark")
    monkeypatch.setattr(app_module, "apply_matplotlib_theme",
                        lambda mode: calls.append(("mpl", mode)))
    monkeypatch.setattr(app_module.plt, "get_fignums", lambda: [1])

    app_module.App._App__change_appearance_mode_event(app, "Dark")

    assert app.appearance_mode == "Dark"
    assert app.list_of_plots == [open_plot]
    assert calls == [("ctk", "Dark"), ("mpl", "Dark"), ("redraw", 1)]


def test_terminal_app_passes_difference_choice_for_two_files(monkeypatch):
    calls = []
    reader = SimpleNamespace(
        energies=[
            SimpleNamespace(info={"SIMULATION-TIME": "TIME",
                                  "PARAMETER": "PARAMETER"}),
            SimpleNamespace(info={"SIMULATION-TIME": "TIME",
                                  "PARAMETER": "PARAMETER"}),
        ],
    )

    class FakePrompt:

        def __init__(self, result):
            self.result = result

        def execute(self):
            return self.result

    class FakeTermPlot:

        def __init__(self, plot_reader):
            self.reader = plot_reader

        def plot(self, info_parameter, difference=False):
            calls.append((self.reader, info_parameter, difference))

    monkeypatch.setattr(termapp_module.inquirer, "select",
                        lambda **kwargs: FakePrompt("PARAMETER"))
    monkeypatch.setattr(termapp_module.inquirer, "confirm",
                        lambda **kwargs: FakePrompt(True))
    monkeypatch.setattr(termapp_module, "TermPlot", FakeTermPlot)

    termapp_module.TermApp(reader).run()

    assert calls == [(reader, "PARAMETER", True)]
