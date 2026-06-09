import numpy as np
import matplotlib.pyplot as plt

from PQEnalyzer.plots.plot_histogram import PlotHistogram
from PQEnalyzer.plots.plot_time import PlotTime


class FakeFlag:

    def __init__(self, value=False):
        self.value = value

    def get(self):
        return self.value


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


class FakeApp:

    def __init__(
        self,
        energies,
        *,
        mean=False,
        median=False,
        cummulative_average=False,
        self_correlation_mean=False,
        running_average=False,
        window_size="",
        filenames=None,
    ):
        self.reader = FakeReader(energies, filenames)
        self.mean = FakeFlag(mean)
        self.median = FakeFlag(median)
        self.cummulative_average = FakeFlag(cummulative_average)
        self.self_correlation_mean = FakeFlag(self_correlation_mean)
        self.running_average = FakeFlag(running_average)
        self.window_size = FakeEntry(window_size)
        self.plot_main_data = FakeFlag(False)


def teardown_function():
    plt.close("all")


def test_histogram_skips_constant_series_and_plots_remaining_data(caplog):
    app = FakeApp([FakeEnergy([1, 1, 1, 1]), FakeEnergy([1, 2, 3, 4])])
    plot = PlotHistogram(app)

    plot.main_data("PARAMETER")

    assert plot.ax.get_legend_handles_labels()[1] == ["series-1.en KDE"]
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


def test_histogram_statistics_draw_single_mean_and_median_lines():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])], mean=True, median=True)
    plot = PlotHistogram(app)

    plot.statistics("PARAMETER")

    assert plot.ax.get_legend_handles_labels()[1] == ["Mean", "Median"]
    assert len(plot.ax.lines) == 2
    assert all(line.get_linestyle() == "--" for line in plot.ax.lines)


def test_time_main_data_uses_readable_filenames_and_value_labels():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])])
    plot = PlotTime(app)

    plot.main_data("PARAMETER")

    assert plot.ax.get_legend_handles_labels()[1] == ["series-0.en"]
    assert len(plot.ax.texts) == 1
    assert plot.ax.texts[0].get_text() == "4.000e+00"


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
