import math
from types import SimpleNamespace

import numpy as np
import matplotlib.pyplot as plt

from PQEnalyzer.plots.plot_dashboard import PlotDashboard
from PQEnalyzer.plots import plot_histogram as plot_histogram_module
from PQEnalyzer.plots.plot_histogram import PlotHistogram
from PQEnalyzer.plots.plot import (
    FOCUSED_RESIZE_DEBOUNCE_MS,
    SINGLE_PLOT_FIGURE_SIZE,
)
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

    def __init__(self, values, unit="unit"):
        self.info = {"PARAMETER": "PARAMETER"}
        self.units = {"PARAMETER": unit}
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


class FakeLargeDashboardEnergy:

    def __init__(self, number_of_parameters=21):
        parameters = [
            f"PARAMETER-{index:02d}"
            for index in range(number_of_parameters)
        ]
        self.info = {
            "SIMULATION-TIME": "SIMULATION-TIME",
            **{parameter: parameter for parameter in parameters},
        }
        self.units = {
            "SIMULATION-TIME": "step",
            **{parameter: "unit" for parameter in parameters},
        }
        self.data = {
            "SIMULATION-TIME": np.array([1, 2, 3]),
            **{
                parameter: np.array([index, index + 1, index + 2])
                for index, parameter in enumerate(parameters)
            },
        }
        self.simulation_time = self.data["SIMULATION-TIME"]
        self.parameters = parameters


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
        self.plot_scale = 1.0
        self.scale_actions = []
        self.remembered_plot_sizes = {}
        self.preferences = SimpleNamespace(
            plot_sizes=self.remembered_plot_sizes)

    def select_plot(self, plot):
        self.selected_plot = plot

    def open_focus_plot(self, parameter):
        self.focus_calls.append(parameter)

    def change_plot_scale(self, action):
        self.scale_actions.append(action)

    def plot_size(self, plot_kind, default):
        return self.remembered_plot_sizes.get(plot_kind, default)

    def remember_plot_size(self, plot_kind, size):
        self.remembered_plot_sizes[plot_kind] = tuple(size)


class FakeScheduledApp(FakeApp):

    def __init__(self, energies):
        super().__init__(energies)
        self.after_calls = []
        self.cancelled_after_ids = []

    def after(self, delay, callback):
        after_id = f"after-{len(self.after_calls)}"
        self.after_calls.append((after_id, delay, callback))
        return after_id

    def after_cancel(self, after_id):
        self.cancelled_after_ids.append(after_id)


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


def test_histogram_reuses_kde_until_data_refresh(monkeypatch):
    app = FakeApp([FakeEnergy([1, 2, 3, 4])])
    plot = PlotHistogram(app)
    plot.info_parameter = "PARAMETER"
    calculation_calls = []

    def calculate_curve(data):
        calculation_calls.append(data.copy())
        return np.array([1.0, 2.0]), np.array([0.2, 0.1])

    monkeypatch.setattr(
        plot_histogram_module,
        "_calculate_kde_curve",
        calculate_curve,
    )

    plot.redraw()
    plot.redraw()

    assert len(calculation_calls) == 1

    plot.refresh(show=False)

    assert len(calculation_calls) == 2


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


def test_single_plot_restores_and_remembers_resized_window():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])])
    app.remembered_plot_sizes["single"] = (9.5, 6.5)
    plot = PlotTime(app)

    np.testing.assert_allclose(plot.figure.get_size_inches(), (9.5, 6.5))

    plot.figure.set_size_inches(12, 8)
    plot._Plot__resize_event(SimpleNamespace())

    np.testing.assert_allclose(
        app.remembered_plot_sizes["single"],
        (12, 8),
    )


def test_single_plot_coalesces_rapid_native_resize_events():
    app = FakeScheduledApp([FakeEnergy([1, 2, 3, 4])])
    plot = PlotTime(app)
    layout_calls = []
    draw_calls = []
    plot.figure.tight_layout = lambda **kwargs: layout_calls.append(kwargs)
    plot.figure.canvas.draw_idle = lambda: draw_calls.append(True)

    plot.figure.set_size_inches(9, 6)
    plot._Plot__resize_event(SimpleNamespace())
    first_after_id, delay, _ = app.after_calls[-1]

    plot.figure.set_size_inches(12, 8)
    plot._Plot__resize_event(SimpleNamespace())
    _, _, final_callback = app.after_calls[-1]

    assert delay == FOCUSED_RESIZE_DEBOUNCE_MS
    assert app.cancelled_after_ids == [first_after_id]
    assert layout_calls == []
    assert draw_calls == []
    np.testing.assert_allclose(
        app.remembered_plot_sizes["single"],
        (12, 8),
    )

    final_callback()

    assert layout_calls == [{"pad": 2.0}]
    assert draw_calls == [True]
    assert plot._resize_after_id is None


def test_single_plot_reuses_layout_until_typography_changes():
    energy = FakeEnergy([1, 2, 3, 4])
    app = FakeApp([energy])
    plot = PlotTime(app)
    plot.info_parameter = "PARAMETER"
    layout_calls = []
    plot.figure.tight_layout = lambda **kwargs: layout_calls.append(kwargs)

    plot.redraw()
    energy.data["PARAMETER"][-1] = 7.0
    plot.redraw()

    assert len(layout_calls) == 1
    assert plot.ax.get_legend_handles_labels()[1] == [
        "series-0.en (7 unit)"
    ]

    app.plot_scale = 1.25
    plot.redraw()
    plot.redraw()

    assert len(layout_calls) == 2


def test_single_plot_keyboard_shortcuts_change_plot_scale():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])])
    plot = PlotTime(app)

    plot._Plot__key_press_event(SimpleNamespace(key="+"))
    plot._Plot__key_press_event(SimpleNamespace(key="cmd+-"))
    plot._Plot__key_press_event(SimpleNamespace(key="x"))

    assert app.scale_actions == ["increase", "decrease"]


def test_single_plot_typography_uses_app_plot_scale():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])])
    app.plot_scale = 1.5
    plot = PlotTime(app)
    plot.info_parameter = "PARAMETER"

    plot.plot_data()

    assert plot.ax._left_title.get_size() == 24
    assert plot.ax.xaxis.label.get_size() == 21
    assert plot.ax.get_xticklabels()[0].get_size() == 18


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


def test_time_plot_omits_missing_qmcfc_unit_from_labels():
    app = FakeApp([FakeEnergy([300, 301, 302], unit=None)])
    plot = PlotTime(app)

    plot.main_data("PARAMETER")
    plot.labels("PARAMETER")

    assert plot.ax.get_ylabel() == "PARAMETER"
    assert plot.ax.get_legend().get_texts()[0].get_text() == (
        "series-0.en (302)"
    )


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
    assert plot.axes[0].get_title(loc="right") == ""
    assert plot.axes[1].get_title(loc="right") == ""
    assert len(plot.axes[0].lines) == 1
    assert len(plot.axes[1].lines) == 1
    assert [text.get_text() for text in plot.axes[0].texts] == ["302 K"]
    assert [text.get_text() for text in plot.axes[1].texts] == ["1.25 bar"]
    assert len(plot.figure.legends) == 1


def test_dashboard_preserves_compact_panel_typography():
    plot = PlotDashboard(FakeApp([FakeDashboardEnergy()]))

    plot.redraw()

    assert plot.axes[0]._left_title.get_fontsize() == 9
    assert plot.axes[0]._left_title.get_fontweight() == "normal"
    assert {
        tick.get_fontsize()
        for tick in plot.axes[0].get_xticklabels()
    } == {8}
    assert {
        tick.get_fontsize()
        for tick in plot.axes[0].get_yticklabels()
    } == {8}


def test_dashboard_places_latest_value_inside_panel():
    plot = PlotDashboard(FakeApp([FakeDashboardEnergy()]))

    plot.redraw()
    plot.figure.canvas.draw()

    readout = plot.axes[0].texts[0]
    assert readout.get_position() == (0.985, 0.965)
    assert readout.get_horizontalalignment() == "right"
    assert readout.get_verticalalignment() == "top"
    assert readout.get_transform() == plot.axes[0].transAxes
    assert readout.get_bbox_patch() is not None

    renderer = plot.figure.canvas.get_renderer()
    axes_bounds = plot.axes[0].get_window_extent(renderer)
    readout_bounds = readout.get_bbox_patch().get_window_extent(renderer)
    title_bounds = plot.axes[0]._left_title.get_window_extent(renderer)
    assert readout_bounds.x0 >= axes_bounds.x0
    assert readout_bounds.x1 <= axes_bounds.x1
    assert readout_bounds.y0 >= axes_bounds.y0
    assert readout_bounds.y1 <= axes_bounds.y1
    assert not readout_bounds.overlaps(title_bounds)


def test_dashboard_bounds_large_parameter_grid_to_screen_shape():
    energy = FakeLargeDashboardEnergy()
    app = FakeApp([energy])
    app.info = energy.parameters

    plot = PlotDashboard(app)

    assert plot._PlotDashboard__grid_shape() == (5, 5)
    assert tuple(plot.figure.get_size_inches()) == (15.0, 9.5)
    assert len(plot.axes) == 25


def test_dashboard_reflows_grid_when_window_shape_changes():
    energy = FakeLargeDashboardEnergy()
    app = FakeApp([energy])
    app.info = energy.parameters
    plot = PlotDashboard(app)

    plot.figure.set_size_inches(6, 10)
    plot._PlotDashboard__resize_event(
        SimpleNamespace(width=600, height=1000))

    assert plot._PlotDashboard__grid_shape() == (7, 3)
    assert plot._grid_shape == (7, 3)
    assert len(plot.axes) == 21

    plot.figure.set_size_inches(16, 6)
    plot._PlotDashboard__resize_event(
        SimpleNamespace(width=1600, height=600))

    assert plot._PlotDashboard__grid_shape() == (4, 6)
    assert plot._grid_shape == (4, 6)
    assert len(plot.axes) == 24
    np.testing.assert_allclose(
        app.remembered_plot_sizes["dashboard"],
        (16, 6),
    )


def test_dashboard_coalesces_rapid_native_resize_events():
    energy = FakeLargeDashboardEnergy()
    app = FakeScheduledApp([energy])
    app.info = energy.parameters
    plot = PlotDashboard(app)

    plot.figure.set_size_inches(6, 10)
    plot._PlotDashboard__resize_event(
        SimpleNamespace(width=600, height=1000))
    first_after_id, delay, _ = app.after_calls[-1]

    plot.figure.set_size_inches(16, 6)
    plot._PlotDashboard__resize_event(
        SimpleNamespace(width=1600, height=600))
    _, _, final_callback = app.after_calls[-1]

    assert delay == 60
    assert app.cancelled_after_ids == [first_after_id]
    assert plot._grid_shape == (5, 5)
    np.testing.assert_allclose(
        app.remembered_plot_sizes["dashboard"],
        (16, 6),
    )

    final_callback()

    assert plot._grid_shape == (4, 6)
    assert plot._pending_resize is None
    assert plot._resize_after_id is None


def test_dashboard_skips_relayout_without_responsive_changes():
    energy = FakeLargeDashboardEnergy(number_of_parameters=11)
    app = FakeScheduledApp([energy])
    app.info = energy.parameters
    plot = PlotDashboard(app)
    redraw_calls = []
    plot.redraw = lambda: redraw_calls.append(True)

    plot.figure.set_size_inches(14, 8)
    plot._PlotDashboard__resize_event(
        SimpleNamespace(width=1400, height=800))
    _, _, callback = app.after_calls[-1]

    callback()

    assert plot._grid_shape == (3, 4)
    assert redraw_calls == []


def test_dashboard_reuses_layout_until_responsive_style_changes():
    energy = FakeDashboardEnergy()
    app = FakeApp([energy])
    plot = PlotDashboard(app)
    layout_calls = []
    plot.figure.tight_layout = lambda **kwargs: layout_calls.append(kwargs)

    plot.redraw()
    energy.data["TEMPERATURE"][-1] = 333.0
    plot.redraw()

    assert len(layout_calls) == 1
    assert plot.axes[0].texts[0].get_text() == "333 K"

    app.plot_scale = 1.25
    plot.redraw()
    plot.redraw()

    assert len(layout_calls) == 2


def test_dashboard_compacts_labels_when_small_without_grid_change():
    energy = FakeLargeDashboardEnergy(number_of_parameters=11)
    app = FakeApp([energy])
    app.info = energy.parameters
    plot = PlotDashboard(app)
    plot.redraw()

    assert plot._grid_shape == (3, 4)
    assert plot._compact_labels is False

    plot.figure.set_size_inches(7, 4.5)
    plot._PlotDashboard__resize_event(
        SimpleNamespace(width=700, height=450))

    assert plot._grid_shape == (3, 4)
    assert plot._compact_labels is True
    assert plot.axes[0].get_title(loc="left") == "PARAMETER-00"


def test_dashboard_growth_never_reduces_average_panel_area():
    energy = FakeLargeDashboardEnergy(number_of_parameters=11)
    app = FakeApp([energy])
    app.info = energy.parameters
    plot = PlotDashboard(app)

    assert plot._grid_shape == (3, 4)
    old_panel_area = (
        plot._canvas_size[0]
        * plot._canvas_size[1]
        / math.prod(plot._grid_shape)
    )

    plot.figure.set_size_inches(16, 6.5)
    plot._PlotDashboard__resize_event(
        SimpleNamespace(width=1600, height=650))

    new_panel_area = 1600 * 650 / math.prod(plot._grid_shape)
    assert plot._grid_shape == (3, 4)
    assert new_panel_area >= old_panel_area


def test_dashboard_updates_compact_typography_without_grid_change():
    energy = FakeLargeDashboardEnergy(number_of_parameters=11)
    app = FakeApp([energy])
    app.info = energy.parameters
    app.plot_scale = 2.0
    plot = PlotDashboard(app)
    plot.redraw()
    initial_font_size = plot.axes[0]._left_title.get_fontsize()
    plot.figure.canvas.draw()
    renderer = plot.figure.canvas.get_renderer()
    initial_bounds = plot.axes[0].get_window_extent(renderer)
    initial_panel_area = initial_bounds.width * initial_bounds.height

    plot.figure.set_size_inches(15, 9)
    plot._PlotDashboard__resize_event(
        SimpleNamespace(width=1500, height=900))
    plot.figure.canvas.draw()
    resized_bounds = plot.axes[0].get_window_extent(
        plot.figure.canvas.get_renderer())
    resized_panel_area = resized_bounds.width * resized_bounds.height

    assert plot._grid_shape == (3, 4)
    assert plot._panel_scale == 1.4
    assert plot.axes[0]._left_title.get_fontsize() > initial_font_size
    assert resized_panel_area >= initial_panel_area


def test_dashboard_switches_dense_large_text_to_compact_labels():
    energy = FakeLargeDashboardEnergy()
    app = FakeApp([energy])
    app.info = energy.parameters
    app.plot_scale = 2.0

    plot = PlotDashboard(app)
    plot.redraw()

    assert plot._grid_shape == (5, 5)
    assert plot._compact_labels is True
    assert plot._panel_scale == 1.0
    assert plot.axes[0].get_title(loc="left") == "PARAMETER-00"
    assert plot.axes[0]._left_title.get_fontsize() == 9
    assert plot.axes[0].texts[0].get_fontsize() == 7.5
    assert plot.figure._suptitle.get_fontsize() == 21
    assert all(
        not label.get_visible()
        for label in plot.axes[0].get_xticklabels()
    )
    assert all(
        label.get_visible()
        for label in plot.axes[20].get_xticklabels()
    )

    plot.figure.canvas.draw()
    renderer = plot.figure.canvas.get_renderer()
    panel_bounds = [
        ax.get_window_extent(renderer)
        for ax in plot.axes[:len(plot.parameters)]
    ]
    assert min(bounds.width for bounds in panel_bounds) > 200
    assert min(bounds.height for bounds in panel_bounds) > 90


def test_dashboard_compacts_multi_file_readout_at_large_scale():
    first = FakeDashboardEnergy()
    second = FakeDashboardEnergy()
    second.data["TEMPERATURE"] = np.array([301.0, 303.0, 304.0])
    second.simulation_time = second.data["SIMULATION-TIME"]
    app = FakeApp([first, second])
    app.plot_scale = 2.0
    plot = PlotDashboard(app)

    plot.redraw()

    assert plot._compact_labels is True
    assert plot.axes[0].get_title(loc="left") == "TEMPERATURE"
    assert plot.axes[0].texts[0].get_text() == "302 K | +1"


def test_dashboard_keyboard_shortcuts_change_plot_scale():
    app = FakeApp([FakeDashboardEnergy()])
    plot = PlotDashboard(app)

    plot._PlotDashboard__key_press_event(SimpleNamespace(key="ctrl+="))
    plot._PlotDashboard__key_press_event(SimpleNamespace(key="0"))
    plot._PlotDashboard__key_press_event(SimpleNamespace(key="x"))

    assert app.scale_actions == ["increase", "reset"]


def test_dashboard_fit_to_screen_uses_native_window_geometry():
    app = FakeApp([FakeDashboardEnergy()])
    plot = PlotDashboard(app)
    geometries = []
    window = SimpleNamespace(
        winfo_screenwidth=lambda: 1920,
        winfo_screenheight=lambda: 1080,
        geometry=geometries.append,
    )
    plot.figure.canvas.manager = SimpleNamespace(window=window)

    assert plot.fit_to_screen() is True
    assert geometries == ["1824x972+48+54"]

    plot._PlotDashboard__key_press_event(SimpleNamespace(key="f"))
    assert geometries == [
        "1824x972+48+54",
        "1824x972+48+54",
    ]


def test_dashboard_uses_custom_independent_axis_label():
    energy = FakeDashboardEnergy()
    energy.axis_label = "Optimization Step"
    app = FakeApp([energy])
    plot = PlotDashboard(app)

    plot.redraw()

    assert plot.axes[-1].get_xlabel() == "Optimization Step"


def test_dashboard_omits_missing_qmcfc_units_from_titles():
    energy = FakeDashboardEnergy()
    energy.units["TEMPERATURE"] = None
    energy.units["PRESSURE"] = None
    app = FakeApp([energy])
    plot = PlotDashboard(app)

    plot.redraw()

    assert plot.axes[0].get_title(loc="left") == "TEMPERATURE"
    assert plot.axes[1].get_title(loc="left") == "PRESSURE"


def test_dashboard_uses_compact_latest_readouts_for_multiple_files():
    first = FakeDashboardEnergy()
    second = FakeDashboardEnergy()
    second.data["TEMPERATURE"] = np.array([301.0, 303.0, 304.0])
    second.simulation_time = second.data["SIMULATION-TIME"]
    app = FakeApp([first, second])
    plot = PlotDashboard(app)

    plot.redraw()

    assert plot.axes[0].get_title(loc="right") == ""
    assert plot.axes[0].texts[0].get_text() == "302 | 304 K"


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
