"""
Textual terminal dashboard for live simulation monitoring.
"""

from dataclasses import dataclass
from datetime import datetime

import numpy as np
from rich.text import Text
from textual.app import App
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Sparkline, Static

from .._logging import get_logger
from ..energy_access import concatenate_series, simulation_time
from ..plots.features import (
    PLOT_FEATURES,
    PLOT_FEATURES_BY_KEY,
    enabled_feature_labels,
)
from ..plots.options import PlotOptions
from ..plots.terminal_chart import build_terminal_chart
from .file_watcher import FileChangeWatcher


logger = get_logger(__name__)


TREND_BLOCKS = "▁▂▃▄▅▆▇█"


@dataclass(frozen=True)
class ParameterSummary:
    """
    Dashboard-ready summary for one parameter.
    """

    parameter: str
    unit: str
    rows: int
    latest: float
    mean: float
    median: float
    std_dev: float
    minimum: float
    maximum: float
    values: np.ndarray

    @property
    def trend(self) -> str:
        """
        Return a compact visual trend for table display.
        """

        return sparkline_text(self.values)


def summarize_parameter(energies, parameter: str) -> ParameterSummary:
    """
    Summarize one parameter across all loaded energy objects.
    """

    energy_series = concatenate_series(energies, parameter)
    values = np.asarray(energy_series.values, dtype=float)

    if values.size == 0:
        latest = mean = median = std_dev = minimum = maximum = float("nan")
    else:
        latest = float(values[-1])
        mean = float(np.nanmean(values))
        median = float(np.nanmedian(values))
        std_dev = float(np.nanstd(values))
        minimum = float(np.nanmin(values))
        maximum = float(np.nanmax(values))

    return ParameterSummary(
        parameter=parameter,
        unit=energy_series.unit,
        rows=int(values.size),
        latest=latest,
        mean=mean,
        median=median,
        std_dev=std_dev,
        minimum=minimum,
        maximum=maximum,
        values=values,
    )


def sparkline_text(values, width=18) -> str:
    """
    Return a small unicode sparkline for a numeric series.
    """

    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return ""

    if values.size > width:
        indices = np.linspace(0, values.size - 1, width).astype(int)
        values = values[indices]

    minimum = float(np.min(values))
    maximum = float(np.max(values))
    if minimum == maximum:
        return TREND_BLOCKS[0] * values.size

    scaled = (values - minimum) / (maximum - minimum)
    block_indices = np.clip(
        np.round(scaled * (len(TREND_BLOCKS) - 1)).astype(int),
        0,
        len(TREND_BLOCKS) - 1,
    )
    return "".join(TREND_BLOCKS[index] for index in block_indices)


def format_value(value) -> str:
    """
    Format a dashboard numeric value compactly without hiding scale.
    """

    if not np.isfinite(value):
        return "n/a"

    magnitude = abs(value)
    if magnitude != 0 and (magnitude < 1e-3 or magnitude >= 1e5):
        return f"{value:.3e}"

    return f"{value:.5g}"


def feature_help_text() -> str:
    """
    Return compact feature help generated from the shared feature registry.
    """

    first_row = "  ".join(
        f"{feature.shortcut} {feature.short_label}"
        for feature in PLOT_FEATURES[:3]
    )
    second_row = "  ".join(
        f"{feature.shortcut} {feature.short_label}"
        for feature in PLOT_FEATURES[3:5]
    )
    third_row = "  ".join(
        f"{feature.shortcut} {feature.short_label}"
        for feature in PLOT_FEATURES[5:]
    )
    return "\n".join([
        "up/j down/k move  enter focus chart",
        "esc back  q quit  r refresh  w watch",
        first_row,
        second_row,
        third_row,
    ])


class ParameterTable(DataTable):
    """
    Data table with vim-style row navigation.
    """

    BINDINGS = [
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
    ]


class TuiApp(App):
    """
    Full-screen terminal dashboard for loaded PQEnalyzer data.
    """

    CSS = """
    Screen {
        background: #0d1117;
        color: #e6edf3;
    }

    #dashboard-view,
    #chart-view {
        height: 1fr;
    }

    #dashboard-main {
        height: 1fr;
    }

    .hidden {
        display: none;
    }

    #analysis-panel {
        height: 17;
    }

    #plot-panel {
        width: 2fr;
        min-width: 58;
    }

    #calculation-panel {
        width: 1fr;
        min-width: 36;
    }

    #status,
    #detail-title,
    #detail-stats,
    #help {
        border: tall #30363d;
        padding: 0 1;
    }

    #status {
        height: 4;
        color: #c9d1d9;
    }

    #parameters {
        height: 1fr;
        border: tall #1f6feb;
    }

    #detail-title {
        height: 3;
        color: #58a6ff;
        text-style: bold;
    }

    #trend {
        height: 1fr;
        border: tall #2ea043;
        padding: 1 1;
    }

    #detail-stats {
        height: 8;
    }

    #help {
        height: 7;
        color: #8b949e;
    }

    #chart-title,
    #chart-controls {
        border: tall #30363d;
        padding: 0 1;
    }

    #chart-title {
        height: 3;
        color: #58a6ff;
        text-style: bold;
    }

    #chart-canvas {
        height: 1fr;
        border: tall #1f6feb;
        padding: 0 0;
        overflow: hidden;
    }

    #chart-controls {
        height: 6;
        color: #8b949e;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("w", "toggle_watch", "Watch"),
        Binding("enter", "show_chart", "Chart"),
        Binding("escape", "show_dashboard", "Dashboard"),
        Binding("j", "select_next_parameter", "Down"),
        Binding("k", "select_previous_parameter", "Up"),
        *[
            Binding(
                feature.shortcut,
                f"toggle_feature('{feature.key}')",
                feature.short_label.title(),
            )
            for feature in PLOT_FEATURES
        ],
    ]

    def __init__(self, reader, watch=True):
        """
        Initialize the terminal dashboard.
        """

        super().__init__()
        self.reader = reader
        self.info = [*self.reader.energies[0].info][1:]
        self.watch_enabled = watch
        self.file_watcher = None
        self.last_refresh = None
        self.refresh_warning = None
        self.summaries = {}
        self.active_view = "dashboard"
        self.chart_options = PlotOptions.with_enabled("mean", "median")
        self.running_average_window_size = 20

    def compose(self):
        """
        Compose the terminal UI layout.
        """

        yield Header(show_clock=True)
        with Vertical(id="dashboard-view"):
            yield Static(id="status")
            with Vertical(id="dashboard-main"):
                yield ParameterTable(id="parameters")
                with Horizontal(id="analysis-panel"):
                    with Vertical(id="plot-panel"):
                        yield Static(id="detail-title")
                        yield Sparkline(id="trend", min_color="#238636",
                                        max_color="#3fb950")
                    with Vertical(id="calculation-panel"):
                        yield Static(id="detail-stats")
                        yield Static(feature_help_text(),
                                     id="help",
                                     markup=False)
        with Vertical(id="chart-view", classes="hidden"):
            yield Static(id="chart-title")
            yield Static(id="chart-canvas")
            yield Static(id="chart-controls")
        yield Footer()

    def on_mount(self) -> None:
        """
        Populate widgets and start watching input files.
        """

        self.title = "PQEnalyzer"
        self.sub_title = "Terminal Dashboard"

        table = self.query_one("#parameters", DataTable)
        table.cursor_type = "row"
        table.add_columns(
            "Parameter",
            "Unit",
            "Rows",
            "Latest",
            "Mean",
            "Min",
            "Max",
        )

        self.refresh_dashboard(read_file=False)
        self.focus_parameter_table()
        if self.watch_enabled:
            self.start_file_watcher()
            self.render_status()

    def on_unmount(self) -> None:
        """
        Stop the file watcher when the terminal app exits.
        """

        self.stop_file_watcher()

    def on_data_table_row_highlighted(
            self, event: DataTable.RowHighlighted) -> None:
        """
        Update the focus panel as the selected parameter changes.
        """

        self.update_detail(event.row_key.value)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """
        Open a focused chart for the selected dashboard row.
        """

        self.update_detail(event.row_key.value)
        self.action_show_chart()

    def action_refresh(self) -> None:
        """
        Force a one-shot file refresh.
        """

        self.refresh_dashboard(read_file=True)

    def action_toggle_watch(self) -> None:
        """
        Toggle file-change watching.
        """

        if self.file_watcher is None:
            if self.start_file_watcher():
                self.watch_enabled = True
        else:
            self.stop_file_watcher()
            self.watch_enabled = False

        self.render_status()

    def action_show_chart(self) -> None:
        """
        Switch to the focused chart view for the selected parameter.
        """

        self.active_view = "chart"
        self.sync_view()
        self.render_chart_controls()
        self.query_one("#chart-canvas", Static).update("Rendering chart...")
        self.call_after_refresh(self.render_chart)

    def action_show_dashboard(self) -> None:
        """
        Switch back to the dashboard view.
        """

        self.active_view = "dashboard"
        self.sync_view()
        self.update_detail(self.selected_parameter())
        self.focus_parameter_table()

    def action_select_next_parameter(self) -> None:
        """
        Select the next parameter using vim-style navigation.
        """

        self.select_relative_parameter(1)

    def action_select_previous_parameter(self) -> None:
        """
        Select the previous parameter using vim-style navigation.
        """

        self.select_relative_parameter(-1)

    def action_toggle_feature(self, feature_key) -> None:
        """
        Toggle one registry-backed chart feature.
        """

        feature = PLOT_FEATURES_BY_KEY[feature_key]
        enabled = not getattr(self.chart_options, feature.option_attribute)
        setattr(self.chart_options, feature.option_attribute, enabled)
        if feature.key == "difference":
            self.chart_options.plot_main = enabled
        self.render_active_statistics()

    def render_active_statistics(self) -> None:
        """
        Refresh statistic controls and the visible data pane.
        """

        self.chart_options.window_size = str(self.running_average_window_size)
        self.render_chart_controls()
        self.update_detail(self.selected_parameter())
        if self.active_view == "chart":
            self.render_chart()

    def start_file_watcher(self) -> bool:
        """
        Start watching loaded input files for changes.
        """

        if self.file_watcher is not None:
            return True

        watcher = FileChangeWatcher(self.reader.filenames,
                                    self.schedule_refresh)
        if watcher.start():
            self.file_watcher = watcher
            self.watch_enabled = True
            return True

        self.watch_enabled = False
        self.refresh_warning = "file watching unavailable"
        return False

    def stop_file_watcher(self) -> None:
        """
        Stop watching loaded input files.
        """

        if self.file_watcher is None:
            return

        self.file_watcher.stop()
        self.file_watcher = None

    def schedule_refresh(self) -> None:
        """
        Schedule a dashboard refresh from a watchdog callback thread.
        """

        try:
            self.call_from_thread(self.refresh_dashboard)
        except RuntimeError:
            self.refresh_dashboard()

    def refresh_dashboard(self, read_file=True) -> None:
        """
        Re-read the latest file and redraw the terminal dashboard.
        """

        if read_file:
            try:
                self.reader.read_last()
            except Exception as error:  # pylint: disable=broad-exception-caught
                self.refresh_warning = str(error)
                logger.warning("TUI refresh skipped: %s", error)
            else:
                self.refresh_warning = None

        self.last_refresh = datetime.now()
        self.summaries = {
            parameter: summarize_parameter(self.reader.energies, parameter)
            for parameter in self.info
        }
        self.render_status()
        self.render_table()
        self.render_chart_controls()
        if self.active_view == "chart":
            self.render_chart()
        else:
            self.update_detail(self.selected_parameter())
            self.focus_parameter_table()

    def sync_view(self) -> None:
        """
        Show the active TUI view and hide the inactive one.
        """

        dashboard = self.query_one("#dashboard-view")
        chart = self.query_one("#chart-view")
        if self.active_view == "chart":
            dashboard.add_class("hidden")
            chart.remove_class("hidden")
        else:
            chart.add_class("hidden")
            dashboard.remove_class("hidden")

    def focus_parameter_table(self) -> None:
        """
        Put keyboard focus back on the parameter table.
        """

        self.query_one("#parameters", DataTable).focus()

    def select_relative_parameter(self, offset: int) -> None:
        """
        Move the selected parameter by a relative row offset.
        """

        table = self.query_one("#parameters", DataTable)
        if table.row_count == 0:
            return

        row_index = min(
            max(table.cursor_row + offset, 0),
            table.row_count - 1,
        )
        table.move_cursor(row=row_index, animate=False)
        self.update_detail(self.selected_parameter())
        if self.active_view == "chart":
            self.render_chart()

    def render_status(self) -> None:
        """
        Render file and watch status.
        """

        updated = (
            self.last_refresh.strftime("%H:%M:%S")
            if self.last_refresh else "never"
        )
        file_rows = [
            f"{filename}: {len(simulation_time(energy))} rows"
            for filename, energy in zip(self.reader.filenames,
                                        self.reader.energies)
        ]

        status = Text()
        status.append("Files ", style="#8b949e")
        status.append(str(len(self.reader.filenames)), style="bold #e6edf3")
        status.append("  Reader ", style="#8b949e")
        status.append(type(self.reader).__name__, style="bold #e6edf3")
        status.append("  Watch ", style="#8b949e")
        status.append(self.watch_label, style="bold #3fb950")
        status.append("  Updated ", style="#8b949e")
        status.append(updated, style="bold #e6edf3")
        status.append("\n")
        status.append(" | ".join(file_rows), style="#c9d1d9")

        if self.refresh_warning:
            status.append("\n")
            status.append(f"Warning: {self.refresh_warning}",
                          style="bold #f85149")

        self.query_one("#status", Static).update(status)

    def render_table(self) -> None:
        """
        Render the parameter overview table.
        """

        table = self.query_one("#parameters", DataTable)
        selected = self.selected_parameter()
        table.clear(columns=False)

        for parameter in self.info:
            summary = self.summaries[parameter]
            table.add_row(
                parameter,
                summary.unit,
                str(summary.rows),
                format_value(summary.latest),
                format_value(summary.mean),
                format_value(summary.minimum),
                format_value(summary.maximum),
                key=parameter,
            )

        if selected is not None and selected in self.summaries:
            row_index = self.info.index(selected)
            table.move_cursor(row=row_index, animate=False)

    def update_detail(self, parameter) -> None:
        """
        Render the detail panel for the selected parameter.
        """

        if not parameter or parameter not in self.summaries:
            return

        summary = self.summaries[parameter]
        title = Text.assemble(
            (parameter, "bold #58a6ff"),
            ("  Unit ", "#8b949e"),
            (summary.unit, "bold #c9d1d9"),
            ("  Rows ", "#8b949e"),
            (str(summary.rows), "bold #c9d1d9"),
        )
        self.query_one("#detail-title", Static).update(title)

        trend = self.query_one("#trend", Sparkline)
        finite_values = summary.values[np.isfinite(summary.values)]
        trend.data = finite_values.tolist()

        stats = "\n".join([
            f"Latest: {format_value(summary.latest)}  "
            f"Mean: {format_value(summary.mean)}",
            f"Median: {format_value(summary.median)}  "
            f"Std: {format_value(summary.std_dev)}",
            f"Min: {format_value(summary.minimum)}  "
            f"Max: {format_value(summary.maximum)}",
            f"Range: {format_value(summary.maximum - summary.minimum)}",
            "",
            f"Chart stats: {self.statistics_label}",
        ])
        self.query_one("#detail-stats", Static).update(stats)

    def render_chart_controls(self) -> None:
        """
        Render the compact statistic control strip under the chart.
        """

        controls = Text()
        controls.append(
            "up/j down/k move  esc back  q quit  r refresh\n",
            style="#8b949e",
        )
        controls.append("Stats: ", style="bold #8b949e")
        for index, feature in enumerate(PLOT_FEATURES):
            if index == len(PLOT_FEATURES) // 2:
                controls.append("\n")
            elif index > 0:
                controls.append(" | ", style="#8b949e")

            enabled = getattr(self.chart_options, feature.option_attribute)
            controls.append(
                f"{feature.shortcut} {feature.short_label} ",
                style="#8b949e",
            )
            controls.append(
                self.enabled_label(enabled),
                style=self.enabled_style(enabled),
            )

        self.query_one("#chart-controls", Static).update(controls)

    def render_chart(self) -> None:
        """
        Render the focused chart for the selected parameter.
        """

        parameter = self.selected_parameter()
        if not parameter:
            return

        summary = self.summaries[parameter]
        self.query_one("#chart-title", Static).update(
            Text.assemble(
                (f"{parameter} / {summary.unit}", "bold #58a6ff"),
                f"  rows {summary.rows}",
                f"  latest {format_value(summary.latest)}",
            ))

        canvas = self.query_one("#chart-canvas", Static)
        size = canvas.content_size
        width = max(48, size.width)
        height = max(14, size.height)
        self.chart_options.window_size = str(self.running_average_window_size)
        try:
            chart = build_terminal_chart(
                self.reader,
                parameter,
                width=width,
                height=height,
                options=self.chart_options,
            )
        except ValueError as error:
            canvas.update(Text(str(error), style="bold #f85149"))
        else:
            canvas.update(Text.from_ansi(chart))

    def selected_parameter(self):
        """
        Return the currently highlighted parameter.
        """

        table = self.query_one("#parameters", DataTable)
        if table.row_count == 0:
            return self.info[0] if self.info else None

        row_index = min(max(table.cursor_row, 0), table.row_count - 1)
        return table.ordered_rows[row_index].key.value

    @property
    def watch_label(self) -> str:
        """
        Return a human-readable watch state.
        """

        if self.file_watcher is not None:
            return "watching for file changes"

        if self.watch_enabled:
            return "watch requested"

        return "paused"

    @property
    def statistics_label(self) -> str:
        """
        Return a compact label for enabled focused-chart statistics.
        """

        active = enabled_feature_labels(self.chart_options)
        return ", ".join(active)

    @staticmethod
    def enabled_label(enabled) -> str:
        """
        Return a short enabled-state label.
        """

        return "on" if enabled else "off"

    @staticmethod
    def enabled_style(enabled) -> str:
        """
        Return the Rich style for an enabled-state label.
        """

        return "bold #3fb950" if enabled else "#8b949e"
