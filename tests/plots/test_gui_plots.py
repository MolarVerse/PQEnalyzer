import numpy as np
import matplotlib.pyplot as plt
from types import SimpleNamespace

from PQEnalyzer.plots.plot_dashboard import PlotDashboard
from PQEnalyzer.plots.plot_histogram import PlotHistogram
from PQEnalyzer.plots.plot import SINGLE_PLOT_FIGURE_SIZE
from PQEnalyzer.plots.plot_time import PlotTime
from PQEnalyzer.plots.theme import PLOT_FONT_SIZES, series_color
from PQEnalyzer.plots.value_readout import (
    ValueReadoutEntry,
    format_readout_value,
    latest_value_label,
)


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


class FakeMissingParameterEnergy:

    def __init__(self):
        self.info = {"OTHER": "OTHER"}
        self.units = {"OTHER": "other-unit"}
        self.data = {"OTHER": np.array([10.0, 11.0, 12.0])}
        self.simulation_time = np.array([1, 2, 3])


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
    assert plot.ax.lines[0].get_color() == series_color(1, "Light")
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


def test_histogram_skips_files_missing_selected_parameter():
    app = FakeApp([
        FakeMissingParameterEnergy(),
        FakeEnergy([1, 2, 3, 4]),
    ])
    plot = PlotHistogram(app)

    plot.main_data("PARAMETER")

    assert plot.ax.get_legend_handles_labels()[1] == ["series-1.en KDE"]
    assert len(plot.ax.collections) == 1
    assert plot.ax.lines[0].get_color() == series_color(1, "Light")


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


def test_time_main_data_uses_readable_filenames_and_latest_readout():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])])
    plot = PlotTime(app)

    plot.main_data("PARAMETER")

    assert plot.ax.get_legend_handles_labels()[1] == [
        "series-0.en (4 unit)"
    ]
    assert plot.ax.lines[0].get_linewidth() == 1.6
    assert plot.ax.lines[0].get_alpha() == 0.92
    assert plot.ax.lines[0].get_zorder() == 2
    assert len(plot.ax.texts) == 0


def test_time_plot_renders_latest_values_in_legend_without_axis_labels():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])],
                  mean=True,
                  median=True)
    plot = PlotTime(app)
    plot.info_parameter = "PARAMETER"

    plot.plot_data()

    assert len(plot.ax.texts) == 0
    assert plot.ax.get_legend_handles_labels()[1] == [
        "series-0.en (4 unit)",
        "Mean (2.5 unit)",
        "Median (2.5 unit)",
    ]
    assert plot.ax.get_legend() is not None
    assert plot.ax.get_legend().get_title().get_text() == ""


def test_time_plot_uses_readable_single_plot_typography():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])])
    plot = PlotTime(app)
    plot.info_parameter = "PARAMETER"

    plot.plot_data()

    assert plot.ax.get_title(loc="left") == "PARAMETER time series"
    assert plot.ax._left_title.get_size() == PLOT_FONT_SIZES["title"]
    assert plot.ax.xaxis.label.get_size() == PLOT_FONT_SIZES["axis_label"]
    assert plot.ax.yaxis.label.get_size() == PLOT_FONT_SIZES["axis_label"]
    assert plot.ax.get_xticklabels()[0].get_size() == PLOT_FONT_SIZES["tick"]
    legend_text = plot.ax.get_legend().get_texts()[0]
    assert legend_text.get_size() == PLOT_FONT_SIZES["legend"]


def test_single_plot_uses_roomier_initial_window_size():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])])
    plot = PlotTime(app)

    np.testing.assert_allclose(
        plot.figure.get_size_inches(),
        SINGLE_PLOT_FIGURE_SIZE,
    )


def test_time_labels_use_time_series_title_and_parameter_axis():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])])
    plot = PlotTime(app)

    plot.main_data("PARAMETER")
    plot.labels("PARAMETER")

    assert plot.ax.get_title(loc="left") == "PARAMETER time series"
    assert plot.ax.get_xlabel() == "Simulation Time"
    assert plot.ax.get_ylabel() == "PARAMETER / unit"


def test_time_labels_use_custom_independent_axis_label():
    energy = FakeEnergy([1, 2, 3, 4])
    energy.axis_label = "Optimization Step"
    app = FakeApp([energy])
    plot = PlotTime(app)

    plot.labels("PARAMETER")

    assert plot.ax.get_xlabel() == "Optimization Step"


def test_time_main_data_disambiguates_duplicate_filenames():
    app = FakeApp(
        [FakeEnergy([1, 2, 3, 4]), FakeEnergy([2, 3, 4, 5])],
        filenames=["/tmp/run-a/md.en", "/tmp/run-b/md.en"],
    )
    plot = PlotTime(app)

    plot.main_data("PARAMETER")

    assert plot.ax.get_legend_handles_labels()[1] == [
        "run-a/md.en (4 unit)",
        "run-b/md.en (5 unit)",
    ]


def test_time_main_data_skips_files_missing_selected_parameter():
    app = FakeApp([
        FakeMissingParameterEnergy(),
        FakeEnergy([1, 2, 3, 4]),
    ])
    plot = PlotTime(app)

    plot.main_data("PARAMETER")

    assert plot.ax.get_legend_handles_labels()[1] == [
        "series-1.en (4 unit)"
    ]
    assert len(plot.ax.lines) == 1
    assert plot.ax.lines[0].get_color() == series_color(1, "Light")


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
        "Mean (2.5 unit)",
        "Median (2.5 unit)",
        "Cumulative Average (2.5 unit)",
        "Self-Correlation Mean (3 unit)",
        "Running Average (2) (3.5 unit)",
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

    assert line.get_label() == "Difference (1 - 2) (3 unit)"
    assert np.all(line.get_xdata() == [1, 2, 3])
    assert np.all(line.get_ydata() == [4, 4, 3])


def test_time_difference_uses_shared_time_axis_values():
    first = FakeEnergy([5, 6, 7])
    second = FakeEnergy([1, 2, 4])
    second.simulation_time = np.array([2, 3, 4])
    app = FakeApp([first, second], difference=True)
    plot = PlotTime(app)

    plot.statistics("PARAMETER")

    assert len(plot.ax.lines) == 1
    line = plot.ax.lines[0]
    assert line.get_label() == "Difference (1 - 2) (5 unit)"
    assert np.all(line.get_xdata() == [2, 3])
    assert np.all(line.get_ydata() == [5, 5])


def test_time_difference_remains_active_when_raw_data_is_visible():
    app = FakeApp(
        [FakeEnergy([5, 6, 7]), FakeEnergy([1, 2, 4])],
        difference=True,
    )
    app.plot_main_data.set(False)
    plot = PlotTime(app)
    plot.info_parameter = "PARAMETER"

    plot.plot_data()

    assert plot.ax.get_legend_handles_labels()[1] == [
        "series-0.en (7 unit)",
        "series-1.en (4 unit)",
        "Difference (1 - 2) (3 unit)",
    ]
    assert len(plot.ax.lines) == 3
    assert np.all(plot.ax.lines[-1].get_ydata() == [4, 4, 3])


def test_time_difference_with_raw_data_uses_overlap_for_shifted_axes():
    first = FakeEnergy([10, 20, 30, 40, 50])
    second = FakeEnergy([3, 5, 7])
    second.simulation_time = np.array([3, 5, 7])
    app = FakeApp([first, second], difference=True)
    app.plot_main_data.set(False)
    plot = PlotTime(app)
    plot.info_parameter = "PARAMETER"

    plot.plot_data()

    assert len(plot.ax.lines) == 3
    np.testing.assert_array_equal(plot.ax.lines[0].get_xdata(),
                                  [1, 2, 3, 4, 5])
    np.testing.assert_array_equal(plot.ax.lines[1].get_xdata(), [3, 5, 7])
    np.testing.assert_array_equal(plot.ax.lines[2].get_xdata(), [3, 5])
    np.testing.assert_array_equal(plot.ax.lines[2].get_ydata(), [27, 45])


def test_time_difference_logs_non_overlapping_series(caplog):
    first = FakeEnergy([5, 6, 7])
    second = FakeEnergy([1, 2, 4])
    second.simulation_time = np.array([20, 30, 40])
    app = FakeApp([first, second], difference=True)
    plot = PlotTime(app)

    plot.statistics("PARAMETER")

    assert len(plot.ax.lines) == 0
    assert "shared simulation-time values" in caplog.text


def test_time_self_correlation_mean_uses_data_scale():
    app = FakeApp([FakeEnergy([1, 2, 3, 4, 5])],
                  self_correlation_mean=True)
    plot = PlotTime(app)

    plot.statistics("PARAMETER")

    line = plot.ax.lines[0]

    assert line.get_label() == "Self-Correlation Mean (4 unit)"
    assert np.all(line.get_xdata() == [1, 2, 3, 4, 5])
    assert np.allclose(line.get_ydata(), [2, 2.5, 3, 3.5, 4])


def test_dashboard_plots_all_parameters_as_raw_overview():
    app = FakeApp([FakeDashboardEnergy()])
    plot = PlotDashboard(app)

    plot.redraw()

    assert plot.axis_parameters[plot.axes[0]] == "TEMPERATURE"
    assert plot.axis_parameters[plot.axes[1]] == "PRESSURE"
    assert plot.axes[0].get_title(loc="left") == "TEMPERATURE / K"
    assert plot.axes[1].get_title(loc="left") == "PRESSURE / bar"
    assert plot.axes[0].get_title(loc="right") == "302 K"
    assert plot.axes[1].get_title(loc="right") == "1.25 bar"
    assert len(plot.axes[0].lines) == 1
    assert len(plot.axes[1].lines) == 1
    assert len(plot.axes[0].texts) == 0
    assert len(plot.axes[1].texts) == 0
    assert len(plot.figure.legends) == 1


def test_dashboard_uses_custom_independent_axis_label():
    energy = FakeDashboardEnergy()
    energy.axis_label = "Optimization Step"
    app = FakeApp([energy])
    plot = PlotDashboard(app)

    plot.redraw()

    assert plot.axes[-1].get_xlabel() == "Optimization Step"


def test_dashboard_uses_compact_latest_titles_for_multiple_files():
    first = FakeDashboardEnergy()
    second = FakeDashboardEnergy()
    second.data["TEMPERATURE"] = np.array([301.0, 303.0, 304.0])
    second.simulation_time = second.data["SIMULATION-TIME"]
    app = FakeApp([first, second])
    plot = PlotDashboard(app)

    plot.redraw()

    assert plot.axes[0].get_title(loc="right") == "302 | 304 K"


def test_dashboard_keeps_file_colors_when_a_parameter_is_missing():
    first = FakeDashboardEnergy()
    first.info.pop("TEMPERATURE")
    first.units.pop("TEMPERATURE")
    first.data.pop("TEMPERATURE")
    second = FakeDashboardEnergy()
    app = FakeApp([first, second])
    plot = PlotDashboard(app)

    plot.redraw()

    assert [line.get_color() for line in plot.axes[0].lines] == [
        series_color(1, "Light")
    ]
    assert [line.get_color() for line in plot.axes[1].lines] == [
        series_color(0, "Light"),
        series_color(1, "Light"),
    ]
    assert [text.get_text() for text in plot.figure.legends[0].get_texts()] == [
        "series-0.en",
        "series-1.en",
    ]


def test_dashboard_shares_full_time_range_across_parameters():
    first = FakeDashboardEnergy()
    first.info.pop("TEMPERATURE")
    first.units.pop("TEMPERATURE")
    first.data.pop("TEMPERATURE")
    first.simulation_time = np.array([0.0, 1.0, 2.0])

    second = FakeDashboardEnergy()
    second.info.pop("PRESSURE")
    second.units.pop("PRESSURE")
    second.data.pop("PRESSURE")
    second.simulation_time = np.array([5.0, 6.0, 7.0])

    plot = PlotDashboard(FakeApp([first, second]))

    plot.redraw()

    np.testing.assert_allclose(plot.axes[0].get_xlim(), (0.0, 7.0))
    np.testing.assert_allclose(plot.axes[1].get_xlim(), (0.0, 7.0))


def test_dashboard_expands_shared_range_for_single_time_value():
    energy = FakeDashboardEnergy()
    energy.simulation_time = np.array([2.0])
    for parameter in ("TEMPERATURE", "PRESSURE"):
        energy.data[parameter] = energy.data[parameter][:1]

    plot = PlotDashboard(FakeApp([energy]))

    plot.redraw()

    np.testing.assert_allclose(plot.axes[0].get_xlim(), (1.5, 2.5))
    np.testing.assert_allclose(plot.axes[1].get_xlim(), (1.5, 2.5))


def test_dashboard_multi_value_title_keeps_mixed_units():
    app = FakeApp([FakeDashboardEnergy()])
    plot = PlotDashboard(app)

    title = plot._PlotDashboard__multi_value_title([
        ValueReadoutEntry("a", 302.0, "#000000", "K"),
        ValueReadoutEntry("b", 1.25, "#000000", "bar"),
    ])

    assert title == "302 K | 1.25 bar"


def test_readout_value_formatting_uses_scientific_notation_selectively():
    assert format_readout_value(302.123456, "K") == "302.12 K"
    assert format_readout_value(0.0000123, "bar") == "1.2300e-05 bar"
    assert format_readout_value(np.nan, "K") == "n/a K"


def test_latest_value_label_uses_last_finite_value():
    assert latest_value_label("Temperature", [300.0, np.nan, 302.0],
                              "K") == "Temperature (302 K)"
    assert latest_value_label("Temperature", [np.nan], "K") == "Temperature"


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
