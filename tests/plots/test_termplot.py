import numpy as np

from PQEnalyzer.plots.termplot import TermPlot


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


def test_termplot_can_plot_difference(monkeypatch):
    calls = []
    reader = FakeReader([FakeEnergy([5, 6, 7]), FakeEnergy([1, 2, 4])])

    monkeypatch.setattr(
        "PQEnalyzer.plots.termplot.plt.plot",
        lambda x, y, label: calls.append(("plot", x, y, label)),
    )
    monkeypatch.setattr(
        "PQEnalyzer.plots.termplot.plt.xlabel",
        lambda value: calls.append(("xlabel", value)),
    )
    monkeypatch.setattr(
        "PQEnalyzer.plots.termplot.plt.ylabel",
        lambda value: calls.append(("ylabel", value)),
    )
    monkeypatch.setattr(
        "PQEnalyzer.plots.termplot.plt.show",
        lambda: calls.append(("show", None)),
    )
    monkeypatch.setattr(
        "PQEnalyzer.plots.termplot.plt.clear_figure",
        lambda: calls.append(("clear", None)),
    )

    TermPlot(reader).plot("PARAMETER", difference=True)

    assert calls[0][0] == "plot"
    np.testing.assert_array_equal(calls[0][1], [1, 2, 3])
    np.testing.assert_array_equal(calls[0][2], [4, 4, 3])
    assert calls[0][3] == "Difference (1 - 2)"
    assert ("xlabel", "Simulation Time") in calls
    assert ("ylabel", "PARAMETER / unit") in calls
    assert calls[-2:] == [("show", None), ("clear", None)]


def test_termplot_logs_invalid_difference_without_plotting(monkeypatch,
                                                          caplog):
    calls = []
    reader = FakeReader([FakeEnergy([5, 6, 7])])

    monkeypatch.setattr(
        "PQEnalyzer.plots.termplot.plt.plot",
        lambda *args, **kwargs: calls.append(("plot", args, kwargs)),
    )
    monkeypatch.setattr(
        "PQEnalyzer.plots.termplot.plt.show",
        lambda: calls.append(("show", None)),
    )
    monkeypatch.setattr(
        "PQEnalyzer.plots.termplot.plt.clear_figure",
        lambda: calls.append(("clear", None)),
    )

    TermPlot(reader).plot("PARAMETER", difference=True)

    assert calls == []
    assert "exactly two input files" in caplog.text
