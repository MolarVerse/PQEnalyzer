import asyncio

import numpy as np
from textual.widgets import DataTable, Static

from PQEnalyzer.apps import tui as tui_module
from PQEnalyzer.apps.tui import (
    TuiApp,
    feature_help_text,
    format_value,
    sparkline_text,
    summarize_parameter,
)
from PQEnalyzer.plots.features import PLOT_FEATURES


class FakeEnergy:

    def __init__(self, values, time=None):
        if time is None:
            time = [1, 2, 3]
        self.info = {"SIMULATION-TIME": "TIME", "PARAMETER": "PARAMETER"}
        self.units = {"PARAMETER": "unit"}
        self.data = {"PARAMETER": np.asarray(values)}
        self.simulation_time = np.asarray(time)


class FakeReader:

    def __init__(self):
        self.filenames = ["run.en"]
        self.energies = [FakeEnergy([1.0, 2.0, 5.0])]

    def read_last(self):
        self.energies = [FakeEnergy([1.0, 3.0, 9.0])]


class FakeMultiParameterEnergy:

    info = {
        "SIMULATION-TIME": "TIME",
        "PARAMETER": "PARAMETER",
        "PRESSURE": "PRESSURE",
    }
    units = {"PARAMETER": "unit", "PRESSURE": "bar"}
    simulation_time = np.asarray([1, 2, 3])
    data = {
        "PARAMETER": np.asarray([1.0, 2.0, 5.0]),
        "PRESSURE": np.asarray([10.0, 20.0, 50.0]),
    }


class FakeMultiParameterReader:

    filenames = ["run.en"]
    energies = [FakeMultiParameterEnergy()]

    def read_last(self):
        self.energies = [FakeMultiParameterEnergy()]


def test_summarize_parameter_keeps_actual_statistics():
    summary = summarize_parameter(
        [FakeEnergy([1.0, 2.0, 5.0]), FakeEnergy([3.0, 8.0])],
        "PARAMETER",
    )

    assert summary.parameter == "PARAMETER"
    assert summary.unit == "unit"
    assert summary.rows == 5
    assert summary.latest == 8.0
    assert summary.mean == 3.8
    assert summary.minimum == 1.0
    assert summary.maximum == 8.0


def test_sparkline_text_samples_series_without_changing_length_limit():
    trend = sparkline_text(np.arange(100), width=10)

    assert len(trend) == 10
    assert trend.startswith("▁")
    assert trend.endswith("█")


def test_format_value_preserves_scale_for_small_and_large_values():
    assert format_value(0.00001) == "1.000e-05"
    assert format_value(1234567) == "1.235e+06"
    assert format_value(12.34567) == "12.346"


def test_tui_feature_bindings_follow_shared_registry():
    binding_keys = {binding.key for binding in TuiApp.BINDINGS}

    assert {
        feature.shortcut
        for feature in PLOT_FEATURES
    }.issubset(binding_keys)
    assert "escape" in binding_keys
    assert "j" in binding_keys
    assert "k" in binding_keys
    assert "b" not in binding_keys
    assert "d" not in binding_keys
    assert "-" not in binding_keys
    assert "+" not in binding_keys
    assert "[" not in binding_keys
    assert "]" not in binding_keys


def test_tui_app_renders_parameter_dashboard():
    app = TuiApp(FakeReader(), watch=False)

    async def run_scenario():
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()

            table = app.query_one("#parameters", DataTable)
            status = app.query_one("#status", Static)
            detail = app.query_one("#detail-stats", Static)
            help_widget = app.query_one("#help", Static)

            assert table.row_count == 1
            assert "run.en: 3 rows" in str(status.content)
            assert "Latest: 5" in str(detail.content)
            assert "Median: 2" in str(detail.content)
            assert "Std:" in str(detail.content)
            assert "Chart stats: mean, median" in str(detail.content)
            assert feature_help_text() == str(help_widget.content)
            assert help_widget._render_markup is False
            assert "up/j down/k move" in str(help_widget.content)
            assert "esc back" in str(help_widget.content)
            assert "- / + window" not in str(help_widget.content)

    asyncio.run(run_scenario())


def test_tui_app_switches_between_dashboard_and_chart():
    app = TuiApp(FakeReader(), watch=False)

    async def run_scenario():
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            chart = app.query_one("#chart-canvas", Static)
            controls = app.query_one("#chart-controls", Static)
            assert app.active_view == "chart"
            assert "PARAMETER / unit" in str(chart.content)
            assert "Simulation Time" in str(chart.content)
            assert "Mean" in str(chart.content)
            assert "Median" in str(chart.content)
            assert "m mean" in str(controls.content)
            assert "up/j down/k move" in str(controls.content)
            assert "esc back" in str(controls.content)
            assert "b back" not in str(controls.content)
            assert "- / +" not in str(controls.content)

            await pilot.press("c")
            await pilot.press("s")
            await pilot.press("a")
            await pilot.pause()

            chart = app.query_one("#chart-canvas", Static)
            controls = app.query_one("#chart-controls", Static)
            assert app.chart_options.cummulative_average is True
            assert app.chart_options.self_correlation_mean is True
            assert app.chart_options.running_average is True
            assert "Cumulative Average" in str(chart.content)
            assert "Self-Correlation Mean" in str(chart.content)
            assert "Running Average (3)" in str(chart.content)
            assert "window" not in str(controls.content)

            await pilot.press("x")
            await pilot.pause()

            chart = app.query_one("#chart-canvas", Static)
            detail = app.query_one("#detail-stats", Static)
            assert app.chart_options.difference is True
            assert app.chart_options.plot_main is True
            assert "exactly two input files" in str(chart.content)
            assert "Chart stats: difference" in str(detail.content)

            await pilot.press("escape")
            await pilot.pause()

            assert app.active_view == "dashboard"

    asyncio.run(run_scenario())


def test_tui_escape_restores_table_focus_and_vim_navigation():
    app = TuiApp(FakeMultiParameterReader(), watch=False)

    async def run_scenario():
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()

            table = app.query_one("#parameters", DataTable)
            detail = app.query_one("#detail-title", Static)
            assert app.focused is table
            assert app.selected_parameter() == "PARAMETER"

            await pilot.press("j")
            await pilot.pause()

            assert app.selected_parameter() == "PRESSURE"
            assert "PRESSURE" in str(detail.content)

            await pilot.press("k")
            await pilot.pause()

            assert app.selected_parameter() == "PARAMETER"

            await pilot.press("enter")
            await pilot.pause()

            chart = app.query_one("#chart-canvas", Static)
            assert app.active_view == "chart"
            assert "PARAMETER / unit" in str(chart.content)

            await pilot.press("j")
            await pilot.pause()

            chart = app.query_one("#chart-canvas", Static)
            assert app.selected_parameter() == "PRESSURE"
            assert "PRESSURE / bar" in str(chart.content)

            await pilot.press("escape")
            await pilot.pause()

            assert app.active_view == "dashboard"
            assert app.focused is table

            await pilot.press("k")
            await pilot.pause()

            assert app.selected_parameter() == "PARAMETER"

            await pilot.press("j")
            await pilot.pause()

            assert app.selected_parameter() == "PRESSURE"

    asyncio.run(run_scenario())


def test_tui_chart_first_render_waits_for_full_layout(monkeypatch):
    app = TuiApp(FakeReader(), watch=False)
    chart_sizes = []

    def fake_build_terminal_chart(reader, parameter, width, height, options):
        chart_sizes.append((width, height))
        return "PARAMETER / unit\nSimulation Time\nMean\nMedian"

    monkeypatch.setattr(
        tui_module,
        "build_terminal_chart",
        fake_build_terminal_chart,
    )

    async def run_scenario():
        async with app.run_test(size=(120, 42)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            assert chart_sizes
            assert chart_sizes[0][0] >= 100
            assert chart_sizes[0][1] >= 25

    asyncio.run(run_scenario())
