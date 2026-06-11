from types import SimpleNamespace

import customtkinter as ctk
import matplotlib.pyplot as plt
import pytest

from PQEnalyzer.apps import app as app_module
from PQEnalyzer.apps import app_layout
from PQEnalyzer.apps import termapp as termapp_module
from PQEnalyzer.plots.options import PlotOptions


class FakeFlag:

    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

    def select(self):
        self.value = True

    def deselect(self):
        self.value = False


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
        self.value = False

    def grid(self, *args, **kwargs):
        self.grid_calls.append((args, kwargs))

    def grid_rowconfigure(self, *args, **kwargs):
        self.configured_rows.append((args, kwargs))

    def grid_columnconfigure(self, *args, **kwargs):
        self.configured_columns.append((args, kwargs))

    def set(self, value):
        self.value = value

    def get(self):
        return self.value

    def select(self):
        self.value = True

    def deselect(self):
        self.value = False

    def configure(self, *args, **kwargs):
        self.configure_args = args
        self.configure_kwargs = kwargs


@pytest.fixture(autouse=True)
def reset_dummy_plots():
    DummyPlot.instances = []


def make_app(auto_refresh=True):
    app = object.__new__(app_module.App)
    app.auto_refresh = FakeFlag(auto_refresh)
    app.reader = SimpleNamespace(filenames=["/tmp/md.en"])
    app.list_of_plots = []
    app.selected_plot = None
    app._App__syncing_plot_controls = False
    app._App__file_watcher = None
    app._App__auto_refresh_after_id = None
    app._App__selected_info = "TEMPERATURE"
    app.after = lambda delay, callback: "after-id"
    app.after_cancel = lambda after_id: None
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


def test_plot_controls_view_exposes_dashboard_button(monkeypatch):
    app = SimpleNamespace(
        register=lambda callback: callback,
        validate_number=lambda value: True,
        toggle_entry_state=lambda event, entry, default="": None,
    )

    monkeypatch.setattr(app_layout.ctk, "CTkFrame", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkCheckBox", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkEntry", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkLabel", FakeWidget)
    monkeypatch.setattr(app_layout.ctk, "CTkButton", FakeWidget)
    monkeypatch.setattr(app_layout.tkinter, "BooleanVar",
                        lambda: FakeFlag(False))

    view = app_layout.PlotControlsView(
        app,
        lambda event: event,
        lambda: None,
    )

    assert app.button_dashboard is view.dashboard_button
    assert app.button_dashboard.kwargs["text"] == "Live Monitor"
    assert app.check_auto_refresh is view.auto_refresh_checkbox
    assert app.check_auto_refresh.kwargs["text"] == "Auto-Refresh"
    assert app.auto_refresh.value is True
    assert not hasattr(app, "button_refresh")


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


def test_statistics_control_callback_runs_after_difference_default(
        monkeypatch):
    calls = []

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

    view = app_layout.StatisticsControlsView(app, lambda: calls.append("run"))
    view.difference.value = True

    view.difference.kwargs["command"]()

    assert app.plot_main_data.value is True
    assert calls == ["run"]


def test_plot_button_runs_simple_time_plot_with_auto_refresh(monkeypatch):
    app = make_app(auto_refresh=True)
    monkeypatch.setattr(app_module, "PlotTime", DummyPlot)

    app_module.App._App__plot_button_event(app, 0)

    assert app.list_of_plots == DummyPlot.instances
    assert DummyPlot.instances[0].calls == [("simple", "TEMPERATURE")]


def test_plot_button_runs_simple_histogram(monkeypatch):
    app = make_app(auto_refresh=False)
    monkeypatch.setattr(app_module, "PlotHistogram", DummyPlot)

    app_module.App._App__plot_button_event(app, 1)

    assert app.list_of_plots == DummyPlot.instances
    assert DummyPlot.instances[0].calls == [("simple", "TEMPERATURE")]


def test_plot_button_runs_dashboard(monkeypatch):
    app = make_app(auto_refresh=False)
    monkeypatch.setattr(app_module, "PlotDashboard", DummyPlot)

    app_module.App._App__plot_button_event(app, 2)

    assert app.list_of_plots == DummyPlot.instances
    assert DummyPlot.instances[0].calls == [("simple", None)]
    assert app.selected_plot is None


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


def test_select_plot_syncs_plot_options_to_controls(monkeypatch):
    app = make_app()
    app.mean = FakeFlag(False)
    app.median = FakeFlag(False)
    app.cummulative_average = FakeFlag(False)
    app.self_correlation_mean = FakeFlag(False)
    app.difference = FakeFlag(False)
    app.running_average = FakeFlag(False)
    app.plot_main_data = FakeFlag(False)
    app.window_size = FakeEntry("")

    plot = SimpleNamespace(
        figure=SimpleNamespace(number=1),
        options=PlotOptions(
            mean=True,
            median=True,
            cummulative_average=True,
            self_correlation_mean=True,
            difference=True,
            running_average=True,
            window_size="25",
            plot_main=True,
        ),
    )
    monkeypatch.setattr(app_module.plt, "get_fignums", lambda: [1])

    app_module.App.select_plot(app, plot)

    assert app.selected_plot is plot
    assert app.mean.value is True
    assert app.median.value is True
    assert app.cummulative_average.value is True
    assert app.self_correlation_mean.value is True
    assert app.difference.value is True
    assert app.running_average.value is True
    assert app.plot_main_data.value is True
    assert app.window_size.value == "25"
    assert app.window_size.state == "normal"


def test_statistics_controls_redraw_selected_plot(monkeypatch):
    app = make_app()
    app.mean = FakeFlag(True)
    app.median = FakeFlag(False)
    app.cummulative_average = FakeFlag(False)
    app.self_correlation_mean = FakeFlag(False)
    app.difference = FakeFlag(False)
    app.running_average = FakeFlag(True)
    app.plot_main_data = FakeFlag(False)
    app.window_size = FakeEntry("5")
    calls = []

    class SelectedPlot:
        figure = SimpleNamespace(number=1)

        def redraw(self, options=None):
            calls.append(options)

    app.selected_plot = SelectedPlot()
    monkeypatch.setattr(app_module.plt, "get_fignums", lambda: [1])

    app_module.App._App__statistics_control_event(app)

    assert len(calls) == 1
    assert calls[0].mean is True
    assert calls[0].running_average is True
    assert calls[0].window_size == "5"


def test_refresh_applies_controls_to_selected_plot(monkeypatch):
    app = make_app()
    app.mean = FakeFlag(False)
    app.median = FakeFlag(False)
    app.cummulative_average = FakeFlag(False)
    app.self_correlation_mean = FakeFlag(False)
    app.difference = FakeFlag(False)
    app.running_average = FakeFlag(True)
    app.plot_main_data = FakeFlag(False)
    app.window_size = FakeEntry("15")

    class SelectedPlot:

        def __init__(self):
            self.figure = SimpleNamespace(number=1)
            self.options = PlotOptions()
            self.refreshed = False

        def refresh(self, show=True):
            self.refreshed = True
            self.show = show

    plot = SelectedPlot()
    app.selected_plot = plot
    app.list_of_plots = [plot]
    monkeypatch.setattr(app_module.plt, "get_fignums", lambda: [1])

    app_module.App._App__refresh_plots(app)

    assert plot.refreshed is True
    assert plot.show is True
    assert plot.options.running_average is True
    assert plot.options.window_size == "15"


def test_auto_refresh_control_starts_and_stops_file_watcher(monkeypatch):
    app = make_app(auto_refresh=True)
    status = FakeWidget()
    app.auto_refresh_status_label = status
    created_watchers = []

    class FakeWatcher:

        def __init__(self, filenames, callback):
            self.filenames = filenames
            self.callback = callback
            self.started = False
            self.stopped = False
            created_watchers.append(self)

        def start(self):
            self.started = True
            return True

        def stop(self):
            self.stopped = True

    monkeypatch.setattr(app_module, "FileChangeWatcher", FakeWatcher)

    app_module.App._App__auto_refresh_control_event(app)

    assert created_watchers[0].filenames == ["/tmp/md.en"]
    assert created_watchers[0].started is True
    assert status.configure_kwargs["text"] == "Watching for file changes"

    app.auto_refresh.set(False)
    app_module.App._App__auto_refresh_control_event(app)

    assert created_watchers[0].stopped is True
    assert app._App__file_watcher is None
    assert status.configure_kwargs["text"] == "Auto-refresh paused"


def test_auto_refresh_control_disables_toggle_when_watcher_unavailable(
        monkeypatch):
    app = make_app(auto_refresh=True)
    status = FakeWidget()
    app.auto_refresh_status_label = status

    class FakeWatcher:

        def __init__(self, filenames, callback):
            pass

        def start(self):
            return False

    monkeypatch.setattr(app_module, "FileChangeWatcher", FakeWatcher)

    app_module.App._App__auto_refresh_control_event(app)

    assert app.auto_refresh.value is False
    assert status.configure_kwargs["text"] == "Auto-refresh unavailable"


def test_auto_refresh_debounces_file_events():
    app = make_app(auto_refresh=True)
    calls = []

    app._App__auto_refresh_after_id = "old"
    app.after_cancel = lambda after_id: calls.append(("cancel", after_id))
    app.after = lambda delay, callback: calls.append(
        ("after", delay, callback.__name__)) or "new"

    app_module.App._App__schedule_auto_refresh(app)

    assert app._App__auto_refresh_after_id == "new"
    assert calls == [
        ("cancel", "old"),
        ("after", 250, "__auto_refresh_plots"),
    ]


def test_auto_refresh_redraws_open_plots_without_show(monkeypatch):
    app = make_app(auto_refresh=True)
    calls = []

    class OpenPlot:
        figure = SimpleNamespace(number=1)

        def refresh(self, show=True):
            calls.append(show)

    app.list_of_plots = [OpenPlot()]
    monkeypatch.setattr(app_module.plt, "get_fignums", lambda: [1])

    app_module.App._App__auto_refresh_plots(app)

    assert app._App__auto_refresh_after_id is None
    assert calls == [False]


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
