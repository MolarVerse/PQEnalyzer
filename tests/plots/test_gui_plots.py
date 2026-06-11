import numpy as np
import matplotlib.pyplot as plt
from types import SimpleNamespace

from PQEnalyzer.plots.plot_dashboard import PlotDashboard
from PQEnalyzer.plots.plot_histogram import PlotHistogram
from PQEnalyzer.plots.plot_time import PlotTime


class FakeFlag:

    def __init__(self, value=False):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeEntry:

    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value


class FakeEnergy:

    def __init__(self, values):
        self.info = {"PARAMETER": "PARAMETER"}
        self.units = {"PARAMETER": "unit"}
        self.data = {"PARAMETER": np.array(values, dtype=float)}
        self.simulation_time = np.arange(1, len(values) + 1)


class FakeDashboardEnergy:

    def __init__(self):
        self.info = {
            "SIMULATION-TIME": "SIMULATION-TIME",
            "TEMPERATURE": "TEMPERATURE",
            "PRESSURE": "PRESSURE",
        }
        self.units = {
            "SIMULATION-TIME": "step",
            "TEMPERATURE": "K",
            "PRESSURE": "bar",
        }
        self.data = {
            "SIMULATION-TIME": np.array([1, 2, 3]),
            "TEMPERATURE": np.array([300.0, 301.0, 302.0]),
            "PRESSURE": np.array([1.0, 1.5, 1.25]),
        }
        self.simulation_time = self.data["SIMULATION-TIME"]


class FakeReader:

    def __init__(self, energies, filenames=None):
        self.energies = energies
        if filenames is None:
            filenames = [
                f"/tmp/series-{index}.en"
                for index, _ in enumerate(energies)
            ]
        self.filenames = filenames

    def read_last(self):
        return None


class FailingReader(FakeReader):

    def read_last(self):
        raise ValueError("file is being written")


class FakeApp:

    def __init__(
        self,
        energies,
        *,
        mean=False,
        median=False,
        cummulative_average=False,
        self_correlation_mean=False,
        difference=False,
        running_average=False,
        window_size="",
        filenames=None,
    ):
        self.reader = FakeReader(energies, filenames)
        self.mean = FakeFlag(mean)
        self.median = FakeFlag(median)
        self.cummulative_average = FakeFlag(cummulative_average)
        self.self_correlation_mean = FakeFlag(self_correlation_mean)
        self.difference = FakeFlag(difference)
        self.running_average = FakeFlag(running_average)
        self.window_size = FakeEntry(window_size)
        self.plot_main_data = FakeFlag(False)
        self.info = ["TEMPERATURE", "PRESSURE"]
        self.focus_calls = []
        self.appearance_mode = "Light"

    def select_plot(self, plot):
        self.selected_plot = plot

    def open_focus_plot(self, parameter):
        self.focus_calls.append(parameter)


def teardown_function():
    plt.close("all")


def test_histogram_skips_constant_series_and_plots_remaining_data(caplog):
    app = FakeApp([FakeEnergy([1, 1, 1, 1]), FakeEnergy([1, 2, 3, 4])])
    plot = PlotHistogram(app)

    plot.main_data("PARAMETER")

    assert plot.ax.get_legend_handles_labels()[1] == ["series-1.en KDE"]
    assert len(plot.ax.collections) == 1
    assert "Data zero. No histogram available." in caplog.text


def test_histogram_disambiguates_duplicate_filenames():
    app = FakeApp(
        [FakeEnergy([1, 2, 3, 4]), FakeEnergy([2, 3, 4, 5])],
        filenames=["/tmp/run-a/md.en", "/tmp/run-b/md.en"],
    )
    plot = PlotHistogram(app)

    plot.main_data("PARAMETER")

    assert plot.ax.get_legend_handles_labels()[1] == [
        "run-a/md.en KDE",
        "run-b/md.en KDE",
    ]
    assert len(plot.ax.collections) == 2


def test_histogram_statistics_draw_single_mean_and_median_lines():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])], mean=True, median=True)
    plot = PlotHistogram(app)

    plot.statistics("PARAMETER")

    assert plot.ax.get_legend_handles_labels()[1] == ["Mean", "Median"]
    assert len(plot.ax.lines) == 2
    assert [line.get_linestyle() for line in plot.ax.lines] == ["--", ":"]
    assert [line.get_zorder() for line in plot.ax.lines] == [4, 4]


def test_histogram_labels_use_distribution_title_and_density_axis():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])])
    plot = PlotHistogram(app)

    plot.main_data("PARAMETER")
    plot.labels("PARAMETER")

    assert plot.ax.get_title(loc="left") == "PARAMETER distribution"
    assert plot.ax.get_xlabel() == "PARAMETER / unit"
    assert plot.ax.get_ylabel() == "Density"
    assert plot.ax.get_ylim()[0] == 0


def test_time_main_data_uses_readable_filenames_and_value_labels():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])])
    plot = PlotTime(app)

    plot.main_data("PARAMETER")

    assert plot.ax.get_legend_handles_labels()[1] == ["series-0.en"]
    assert plot.ax.lines[0].get_linewidth() == 1.6
    assert plot.ax.lines[0].get_alpha() == 0.92
    assert plot.ax.lines[0].get_zorder() == 2
    assert len(plot.ax.texts) == 1
    assert plot.ax.texts[0].get_text() == "4.000e+00"


def test_time_labels_use_time_series_title_and_parameter_axis():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])])
    plot = PlotTime(app)

    plot.main_data("PARAMETER")
    plot.labels("PARAMETER")

    assert plot.ax.get_title(loc="left") == "PARAMETER time series"
    assert plot.ax.get_xlabel() == "Simulation step"
    assert plot.ax.get_ylabel() == "PARAMETER / unit"


def test_time_main_data_disambiguates_duplicate_filenames():
    app = FakeApp(
        [FakeEnergy([1, 2, 3, 4]), FakeEnergy([2, 3, 4, 5])],
        filenames=["/tmp/run-a/md.en", "/tmp/run-b/md.en"],
    )
    plot = PlotTime(app)

    plot.main_data("PARAMETER")

    assert plot.ax.get_legend_handles_labels()[1] == [
        "run-a/md.en",
        "run-b/md.en",
    ]


def test_running_average_rejects_invalid_window_size_without_crashing(caplog):
    app = FakeApp([FakeEnergy([1, 2, 3, 4])],
                  running_average=True,
                  window_size="0")
    plot = PlotTime(app)

    plot.statistics("PARAMETER")

    assert "Window size must be positive" in caplog.text


def test_time_statistics_draw_expected_overlay_series():
    app = FakeApp(
        [FakeEnergy([1, 2, 3, 4])],
        mean=True,
        median=True,
        cummulative_average=True,
        self_correlation_mean=True,
        running_average=True,
        window_size="2",
    )
    plot = PlotTime(app)

    plot.statistics("PARAMETER")

    assert plot.ax.get_legend_handles_labels()[1] == [
        "Mean",
        "Median",
        "Cumulative Average",
        "Self-Correlation Mean",
        "Running Average (2)",
    ]
    assert [line.get_linestyle() for line in plot.ax.lines[:3]] == [
        "--",
        ":",
        "-.",
    ]
    assert plot.ax.lines[-1].get_linestyle() == "-"
    assert plot.ax.lines[-1].get_zorder() == 4


def test_time_difference_subtracts_two_aligned_series():
    app = FakeApp(
        [FakeEnergy([5, 6, 7]), FakeEnergy([1, 2, 4])],
        difference=True,
        mean=True,
    )
    plot = PlotTime(app)

    plot.statistics("PARAMETER")

    assert len(plot.ax.lines) == 1
    line = plot.ax.lines[0]

    assert line.get_label() == "Difference (1 - 2)"
    assert np.all(line.get_xdata() == [1, 2, 3])
    assert np.all(line.get_ydata() == [4, 4, 3])


def test_time_difference_logs_misaligned_series(caplog):
    first = FakeEnergy([5, 6, 7])
    second = FakeEnergy([1, 2, 4])
    second.simulation_time = np.array([2, 3, 4])
    app = FakeApp([first, second], difference=True)
    plot = PlotTime(app)

    plot.statistics("PARAMETER")

    assert len(plot.ax.lines) == 0
    assert "matching simulation-time axes" in caplog.text


def test_time_self_correlation_mean_uses_data_scale():
    app = FakeApp([FakeEnergy([1, 2, 3, 4, 5])],
                  self_correlation_mean=True)
    plot = PlotTime(app)

    plot.statistics("PARAMETER")

    line = plot.ax.lines[0]

    assert line.get_label() == "Self-Correlation Mean"
    assert np.all(line.get_xdata() == [1, 2, 3, 4, 5])
    assert np.allclose(line.get_ydata(),
                       [8.6666, 10, 11, 10, 8.6666],
                       rtol=1e-4)


def test_dashboard_plots_all_parameters_as_raw_overview():
    app = FakeApp([FakeDashboardEnergy()])
    plot = PlotDashboard(app)

    plot.redraw()

    assert plot.axis_parameters[plot.axes[0]] == "TEMPERATURE"
    assert plot.axis_parameters[plot.axes[1]] == "PRESSURE"
    assert plot.axes[0].get_title(loc="left") == "TEMPERATURE / K"
    assert plot.axes[1].get_title(loc="left") == "PRESSURE / bar"
    assert len(plot.axes[0].lines) == 1
    assert len(plot.axes[1].lines) == 1
    assert len(plot.figure.legends) == 1


def test_dashboard_double_click_opens_focused_parameter_plot():
    app = FakeApp([FakeDashboardEnergy()])
    plot = PlotDashboard(app)
    plot.redraw()

    event = SimpleNamespace(dblclick=True, inaxes=plot.axes[1])

    plot._PlotDashboard__button_press_event(event)

    assert app.focus_calls == ["PRESSURE"]


def test_dashboard_single_click_highlights_panel_without_opening_focus():
    app = FakeApp([FakeDashboardEnergy()])
    plot = PlotDashboard(app)
    plot.redraw()

    event = SimpleNamespace(dblclick=False, inaxes=plot.axes[1])

    plot._PlotDashboard__button_press_event(event)

    assert plot.selected_parameter == "PRESSURE"
    assert app.focus_calls == []
    assert all(
        np.isclose(spine.get_linewidth(), 2.1)
        for spine in plot.axes[1].spines.values()
    )
    assert all(
        np.isclose(spine.get_linewidth(), 1.0)
        for spine in plot.axes[0].spines.values()
    )


def test_dashboard_refresh_keeps_existing_plot_on_read_error(caplog):
    app = FakeApp([FakeDashboardEnergy()])
    app.reader = FailingReader([FakeDashboardEnergy()])
    plot = PlotDashboard(app)
    plot.redraw()

    plot.refresh()

    assert "Dashboard refresh skipped: file is being written" in caplog.text
    assert "refresh skipped: file is being written" in plot.subtitle_text.get_text()
    assert len(plot.axes[0].lines) == 1
