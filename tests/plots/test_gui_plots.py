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

    def __init__(self, energies):
        self.energies = energies
        self.filenames = [
            f"/tmp/series-{index}.en" for index, _ in enumerate(energies)
        ]

    def read_last(self):
        return None


class FakeApp:

    def __init__(
        self,
        energies,
        *,
        mean=False,
        median=False,
        running_average=False,
        window_size="",
    ):
        self.reader = FakeReader(energies)
        self.mean = FakeFlag(mean)
        self.median = FakeFlag(median)
        self.cummulative_average = FakeFlag(False)
        self.auto_correlation = FakeFlag(False)
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


def test_histogram_statistics_draw_single_mean_and_median_lines():
    app = FakeApp([FakeEnergy([1, 2, 3, 4])], mean=True, median=True)
    plot = PlotHistogram(app)

    plot.statistics("PARAMETER")

    assert len(plot.ax.collections) == 2
    assert len(plot.ax.collections[0].get_segments()) == 1
    assert len(plot.ax.collections[1].get_segments()) == 1


def test_running_average_rejects_invalid_window_size_without_crashing(caplog):
    app = FakeApp([FakeEnergy([1, 2, 3, 4])],
                  running_average=True,
                  window_size="0")
    plot = PlotTime(app)

    plot.statistics("PARAMETER")

    assert "Window size must be positive" in caplog.text
