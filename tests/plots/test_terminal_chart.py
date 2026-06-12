import numpy as np

from PQEnalyzer.plots.terminal_chart import build_terminal_chart
from PQEnalyzer.plots.options import PlotOptions


class FakeEnergy:

    def __init__(self, values, time=None):
        if time is None:
            time = [1, 2, 3]
        self.info = {"PARAMETER": "PARAMETER"}
        self.units = {"PARAMETER": "unit"}
        self.data = {"PARAMETER": np.array(values)}
        self.simulation_time = np.array(time)


class FakeReader:

    def __init__(self, energies):
        self.energies = energies
        self.filenames = [f"/tmp/run-{index}.en"
                          for index, _ in enumerate(energies)]


def test_terminal_chart_contains_labels_and_series_name():
    reader = FakeReader([FakeEnergy([1.0, 2.0, 5.0])])

    chart = build_terminal_chart(reader, "PARAMETER", width=48, height=12)

    assert "PARAMETER / unit" in chart
    assert "Simulation Time" in chart
    assert "run-0.en" in chart


def test_terminal_chart_can_render_statistic_overlays():
    reader = FakeReader([FakeEnergy([1.0, 2.0, 4.0, 8.0, 16.0])])
    options = PlotOptions(
        mean=True,
        median=True,
        cummulative_average=True,
        self_correlation_mean=True,
        running_average=True,
        window_size="3",
    )

    chart = build_terminal_chart(
        reader,
        "PARAMETER",
        width=100,
        height=24,
        options=options,
    )

    assert "Mean" in chart
    assert "Median" in chart
    assert "Cumulative Average" in chart
    assert "Self-Correlation Mean" in chart
    assert "Running Average (3)" in chart


def test_terminal_chart_clamps_running_average_window_to_data_length():
    reader = FakeReader([FakeEnergy([1.0, 2.0, 5.0])])
    options = PlotOptions(running_average=True, window_size="20")

    chart = build_terminal_chart(
        reader,
        "PARAMETER",
        width=72,
        height=16,
        options=options,
    )

    assert "Running Average (3)" in chart
