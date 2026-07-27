"""
Live dashboard plotting for all available time-series parameters.
"""

import math
import signal

import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np

from .._logging import get_logger
from ..energy_access import (
    axis_label,
    has_parameter,
    parameter_unit_for_energies,
    series,
)
from ..preferences import plot_scale_action
from .labels import parameter_label, unique_path_labels
from .theme import (
    apply_figure_theme,
    apply_matplotlib_theme,
    palette_for_appearance_mode,
    scaled_font_size,
    series_color,
)
from .value_readout import ValueReadoutEntry, format_readout_value


logger = get_logger(__name__)
RESIZE_DEBOUNCE_MS = 120


class PlotDashboard:
    """
    Render a raw overview grid for every parameter in the reader.
    """

    def __init__(self, app):
        """
        Create a dashboard figure for all selectable app parameters.
        """

        self.app = app
        self.reader = app.reader
        self.parameters = list(app.info)
        self.axis_parameters = {}
        self.latest_values = {}
        self.selected_parameter = None
        self.refresh_warning = None
        self.subtitle_text = None
        self._panel_scale = 1.0
        self._compact_labels = False
        self._pending_resize = None
        self._resize_after_id = None

        apply_matplotlib_theme(
            getattr(self.app, "appearance_mode", None),
            getattr(self.app, "plot_scale", 1.0),
        )
        default_figure_size = self.__figure_size()
        saved_plot_sizes = getattr(
            getattr(self.app, "preferences", None),
            "plot_sizes",
            {},
        )
        self._fit_on_first_open = "dashboard" not in saved_plot_sizes
        figure_size = (
            self.app.plot_size("dashboard", default_figure_size)
            if hasattr(self.app, "plot_size")
            else default_figure_size
        )
        self.figure = plt.figure(figsize=figure_size)
        self._canvas_size = tuple(
            dimension * self.figure.dpi
            for dimension in self.figure.get_size_inches()
        )
        self._grid_shape = self.__grid_shape()
        self.axes = self.__create_axes(self._grid_shape)
        self.ani = None
        self.__set_window_title()

        signal.signal(
            signal.SIGINT,
            lambda signal, frame: self.signal_handler(signal, frame),
        )
        self.figure.canvas.mpl_connect("button_press_event",
                                       self.__button_press_event)
        self.figure.canvas.mpl_connect(
            "key_press_event",
            self.__key_press_event,
        )
        self.figure.canvas.mpl_connect(
            "resize_event",
            self.__resize_event,
        )

    def signal_handler(self, signal, frame):
        """
        Close plot and application windows after SIGINT.
        """

        plt.close("all")
        self.app.destroy()

    def simple(self, info_parameter=None) -> None:
        """
        Render a static dashboard.
        """

        self.redraw()
        if self._fit_on_first_open:
            self.fit_to_screen()
            self._fit_on_first_open = False
        plt.show()

    def follow(self, info_parameter=None, interval: float = 1.0) -> None:
        """
        Render a live dashboard and refresh it at the configured interval.
        """

        def update(frame):
            self.__safe_read_last()
            self.redraw()
            return []

        self.redraw()
        if self._fit_on_first_open:
            self.fit_to_screen()
            self._fit_on_first_open = False
        self.ani = animation.FuncAnimation(
            self.figure,
            update,
            blit=True,
            interval=interval * 1000,
            cache_frame_data=False,
        )
        plt.show()

    def refresh(self, show=True) -> None:
        """
        Refresh the dashboard while keeping the previous view on read errors.
        """

        if not self.__safe_read_last():
            self.__set_title()
            self.figure.canvas.draw_idle()
            return None

        self.redraw()
        if show:
            plt.show()

    def redraw(self) -> None:
        """
        Redraw all raw parameter panels.
        """

        self.__reflow_axes()
        self._panel_scale = self.__panel_scale()
        requested_scale = getattr(self.app, "plot_scale", 1.0)
        self._compact_labels = self._panel_scale < requested_scale - 0.05
        for ax in self.axes:
            ax.clear()
            apply_figure_theme(
                self.figure,
                ax,
                getattr(self.app, "appearance_mode", None),
                self._panel_scale,
            )

        self.axis_parameters = {}
        self.latest_values = {}
        labels = unique_path_labels(self.reader.filenames)

        for index, parameter in enumerate(self.parameters):
            ax = self.axes[index]
            self.axis_parameters[ax] = parameter
            self.__plot_parameter(ax, parameter, labels)
            self.__label_axis(ax, parameter, index)
            self.__style_axis(ax, parameter)

        self.__apply_shared_x_limits()

        for ax in self.axes[len(self.parameters):]:
            ax.set_visible(False)

        for legend in list(self.figure.legends):
            legend.remove()
        self.__show_legend(labels)
        self.__set_title()
        self.__fit_layout()
        self.figure.canvas.draw_idle()

    def __plot_parameter(self, ax, parameter, labels):
        """
        Plot one raw parameter panel.
        """

        for index, energy in enumerate(self.reader.energies):
            if not has_parameter(energy, parameter):
                continue

            energy_series = series(energy, parameter)
            line = ax.plot(
                energy_series.time,
                energy_series.values,
                label=labels[index],
                color=series_color(
                    index,
                    getattr(self.app, "appearance_mode", None),
                ),
                linewidth=1.45,
                alpha=0.92,
            )[0]
            self.__add_latest_value(
                parameter,
                labels[index],
                line,
                energy_series.values,
            )

    def __label_axis(self, ax, parameter, index):
        """
        Label one dashboard axis compactly.
        """

        unit = parameter_unit_for_energies(self.reader.energies, parameter)
        palette = palette_for_appearance_mode(
            getattr(self.app, "appearance_mode", None))
        plot_scale = self._panel_scale
        title_unit = None if self._compact_labels else unit
        ax.set_title(
            parameter_label(parameter, title_unit),
            fontsize=scaled_font_size(9, plot_scale),
            fontweight="normal",
            loc="left",
            pad=6,
        )
        ax.text(
            0.985,
            0.965,
            self.__latest_value_title(parameter),
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=scaled_font_size(7.5, plot_scale),
            fontfamily="monospace",
            color=palette["subtle.text"],
            bbox={
                "boxstyle": (
                    "square,pad=0.12"
                    if self._compact_labels
                    else "round,pad=0.22"
                ),
                "facecolor": palette["annotation.facecolor"],
                "edgecolor": "none",
                "alpha": 0.72 if self._compact_labels else 0.82,
            },
            clip_on=True,
            zorder=5,
        )
        ax.ticklabel_format(
            axis="both",
            style="sci",
            scilimits=(-3, 3),
            useOffset=True,
        )
        number_of_ticks = 3 if self._compact_labels else 4
        ax.xaxis.set_major_locator(
            MaxNLocator(nbins=number_of_ticks, min_n_ticks=2))
        ax.yaxis.set_major_locator(
            MaxNLocator(nbins=number_of_ticks, min_n_ticks=2))
        ax.tick_params(labelsize=scaled_font_size(8, plot_scale))
        ax.xaxis.get_offset_text().set_fontsize(
            scaled_font_size(7, plot_scale))
        ax.yaxis.get_offset_text().set_fontsize(
            scaled_font_size(7, plot_scale))

        nrows, ncols = self._grid_shape
        bottom_row = index // ncols == nrows - 1
        ax.tick_params(axis="x", labelbottom=bottom_row)
        ax.xaxis.get_offset_text().set_visible(bottom_row)
        if bottom_row:
            ax.set_xlabel(
                axis_label(self.reader.energies[0]),
                fontsize=scaled_font_size(8, plot_scale),
            )

    def __add_latest_value(self, parameter, label, line, values):
        """
        Store one dashboard line's latest value for its panel readout.
        """

        if len(values) == 0:
            return

        unit = parameter_unit_for_energies(self.reader.energies, parameter)
        self.latest_values.setdefault(parameter, []).append(
            ValueReadoutEntry(
                label=label,
                value=float(values[-1]),
                color=line.get_color(),
                unit=unit,
            ))

    def __latest_value_title(self, parameter):
        """
        Return the compact latest-value text for a dashboard panel.
        """

        entries = self.latest_values.get(parameter, [])
        if not entries:
            return ""

        if self._compact_labels and len(entries) > 1:
            return f"{entries[0].formatted_value} | +{len(entries) - 1}"

        if len(entries) == 1:
            return entries[0].formatted_value

        visible_entries = entries[:2]
        title = self.__multi_value_title(visible_entries)
        remaining = len(entries) - len(visible_entries)
        if remaining > 0:
            title = f"{title} | +{remaining}"
        return title

    def __multi_value_title(self, entries):
        """
        Return compact values for multi-file dashboard headers.
        """

        units = {entry.unit for entry in entries if entry.unit}
        if len(units) == 1:
            unit = entries[0].unit
            values = " | ".join(
                format_readout_value(entry.value) for entry in entries)
            return f"{values} {unit}".rstrip()

        return " | ".join(entry.formatted_value for entry in entries)

    def __show_legend(self, file_labels):
        """
        Draw one shared legend containing every plotted input file.
        """

        handles_by_label = {}
        for ax in self.axes:
            handles, labels = ax.get_legend_handles_labels()
            for handle, label in zip(handles, labels):
                handles_by_label.setdefault(label, handle)

        labels = [
            label for label in file_labels if label in handles_by_label
        ]
        if labels:
            self.figure.legend(
                [handles_by_label[label] for label in labels],
                labels,
                loc="upper right",
                bbox_to_anchor=(0.995, 0.985),
                ncol=min(4, len(labels)),
                fontsize=scaled_font_size(
                    9,
                    self.__header_scale(1.25),
                ),
                frameon=True,
            )
            return

        logger.warning("No data to plot.")

    def __apply_shared_x_limits(self):
        """
        Apply the full plotted time range to every dashboard panel.
        """

        x_values = []
        for ax in self.axes[:len(self.parameters)]:
            for line in ax.lines:
                values = np.asarray(line.get_xdata(), dtype=float)
                x_values.extend(values[np.isfinite(values)])

        if not x_values:
            return

        lower = min(x_values)
        upper = max(x_values)
        if lower == upper:
            margin = max(abs(lower) * 0.05, 0.5)
            lower -= margin
            upper += margin

        for ax in self.axes[:len(self.parameters)]:
            ax.set_xlim(lower, upper)

    def __safe_read_last(self):
        """
        Read the growing output file without closing the dashboard on failures.
        """

        try:
            self.reader.read_last()
        except Exception as error:  # pylint: disable=broad-exception-caught
            self.refresh_warning = str(error)
            logger.warning("Dashboard refresh skipped: %s", error)
            return False

        self.refresh_warning = None
        return True

    def __button_press_event(self, event):
        """
        Open a focused plot when a dashboard panel is double-clicked.
        """

        parameter = self.axis_parameters.get(event.inaxes)
        if parameter is None:
            return

        self.selected_parameter = parameter
        for ax, axis_parameter in self.axis_parameters.items():
            self.__style_axis(ax, axis_parameter)
        self.figure.canvas.draw_idle()

        if getattr(event, "dblclick", False):
            self.app.open_focus_plot(parameter)

    def __key_press_event(self, event):
        """
        Apply plot scaling or fit the dashboard to the screen.
        """

        key = (getattr(event, "key", None) or "").lower()
        if key == "f":
            self.fit_to_screen()
            return

        action = plot_scale_action(key)
        if action is not None and hasattr(self.app, "change_plot_scale"):
            self.app.change_plot_scale(action)

    def fit_to_screen(self):
        """
        Fit the native dashboard window to the current display.
        """

        manager = getattr(self.figure.canvas, "manager", None)
        window = getattr(manager, "window", None)
        if window is None:
            return False

        if hasattr(window, "showMaximized"):
            window.showMaximized()
            return True

        if not all(
            hasattr(window, attribute)
            for attribute in (
                "geometry",
                "winfo_screenwidth",
                "winfo_screenheight",
            )
        ):
            return False

        screen_width = int(window.winfo_screenwidth())
        screen_height = int(window.winfo_screenheight())
        horizontal_margin = max(20, round(screen_width * 0.025))
        vertical_margin = max(40, round(screen_height * 0.05))
        width = screen_width - 2 * horizontal_margin
        height = screen_height - 2 * vertical_margin
        window.geometry(
            f"{width}x{height}+{horizontal_margin}+{vertical_margin}"
        )
        return True

    def __resize_event(self, event):
        """
        Remember the window size and coalesce expensive dashboard relayouts.
        """

        width = getattr(event, "width", None)
        height = getattr(event, "height", None)
        self._pending_resize = width, height

        if hasattr(self.app, "remember_plot_size"):
            self.app.remember_plot_size(
                "dashboard",
                self.figure.get_size_inches(),
            )

        schedule = getattr(self.app, "after", None)
        cancel = getattr(self.app, "after_cancel", None)
        if not callable(schedule) or not callable(cancel):
            self.__apply_pending_resize()
            return

        if self._resize_after_id is not None:
            cancel(self._resize_after_id)
        self._resize_after_id = schedule(
            RESIZE_DEBOUNCE_MS,
            self.__apply_pending_resize,
        )

    def __apply_pending_resize(self):
        """
        Apply the final layout after a burst of native resize events.
        """

        self._resize_after_id = None
        if self._pending_resize is None:
            return

        width, height = self._pending_resize
        self._pending_resize = None
        if self.figure.number not in plt.get_fignums():
            return

        grid_changed = self.__reflow_axes(width, height)
        panel_scale = self.__panel_scale()
        requested_scale = getattr(self.app, "plot_scale", 1.0)
        compact_labels = panel_scale < requested_scale - 0.05
        style_changed = (
            panel_scale != self._panel_scale
            or compact_labels != self._compact_labels
        )
        if grid_changed or style_changed:
            self.redraw()
        else:
            self.__fit_layout()
            self.figure.canvas.draw_idle()

    def __create_axes(self, grid_shape):
        """
        Create enough axes for all dashboard parameters.
        """

        nrows, ncols = grid_shape
        axes = self.figure.subplots(nrows=nrows, ncols=ncols, squeeze=False)
        return list(axes.flat)

    def __grid_shape(self, width=None, height=None):
        """
        Return a responsive grid for the current window shape.
        """

        if width is None or height is None:
            figure = getattr(self, "figure", None)
            if figure is None:
                width, height = 15.0, 9.5
            else:
                width, height = figure.get_size_inches()

        width = max(float(width), 1.0)
        height = max(float(height), 1.0)
        number_of_parameters = max(1, len(self.parameters))
        target_panel_aspect = 1.45

        candidates = []
        for ncols in range(1, min(6, number_of_parameters) + 1):
            nrows = math.ceil(number_of_parameters / ncols)
            panel_aspect = (width / ncols) / (height / nrows)
            aspect_error = abs(
                math.log(panel_aspect / target_panel_aspect)
            )
            empty_ratio = (
                nrows * ncols - number_of_parameters
            ) / number_of_parameters
            score = aspect_error + 0.8 * empty_ratio
            candidates.append((score, nrows * ncols, nrows, ncols))

        _, _, nrows, ncols = min(candidates)
        return nrows, ncols

    def __figure_size(self):
        """
        Return a readable figure size for the current parameter count.
        """

        nrows, ncols = self.__grid_shape(15.0, 9.5)
        width = min(15.0, max(8.5, 3.1 * ncols))
        height = min(9.5, max(4.8, 2.2 * nrows + 1.2))
        return width, height

    def __panel_scale(self):
        """
        Cap dense panel typography by the available canvas area.
        """

        requested_scale = float(getattr(self.app, "plot_scale", 1.0))
        if requested_scale <= 1.0:
            return requested_scale

        width, height = self._canvas_size
        nrows, ncols = self._grid_shape
        panel_width = width / ncols
        panel_height = height * 0.82 / nrows
        width_capacity = max(1.0, panel_width / 260)
        height_capacity = max(1.0, panel_height / 170)
        panel_scale = min(
            requested_scale,
            width_capacity,
            height_capacity,
            1.5,
        )
        return math.floor(panel_scale * 20 + 1e-9) / 20

    def __header_scale(self, maximum):
        """
        Return a bounded scale for shared dashboard header elements.
        """

        return min(float(getattr(self.app, "plot_scale", 1.0)), maximum)

    def __reflow_axes(self, width=None, height=None):
        """
        Recreate dashboard axes when the responsive grid shape changes.
        """

        if width is None or height is None:
            width, height = (
                dimension * self.figure.dpi
                for dimension in self.figure.get_size_inches()
            )
        width = max(float(width), 1.0)
        height = max(float(height), 1.0)
        grid_shape = self.__grid_shape(width, height)
        previous_width, previous_height = self._canvas_size
        previous_slots = self._grid_shape[0] * self._grid_shape[1]
        candidate_slots = grid_shape[0] * grid_shape[1]
        previous_panel_area = (
            previous_width * previous_height / previous_slots
        )
        candidate_panel_area = width * height / candidate_slots
        window_grew = width * height >= previous_width * previous_height
        if window_grew and candidate_panel_area < previous_panel_area:
            grid_shape = self._grid_shape

        self._canvas_size = width, height
        if grid_shape == self._grid_shape:
            return False

        self.figure.clear()
        self.subtitle_text = None
        self.axis_parameters = {}
        self._grid_shape = grid_shape
        self.axes = self.__create_axes(grid_shape)
        return True

    def __fit_layout(self):
        """
        Refit dashboard labels to the current canvas dimensions.
        """

        self.figure.tight_layout(
            rect=(0, 0.03, 1, 0.92),
            h_pad=0.7,
            w_pad=0.8,
        )

    def __style_axis(self, ax, parameter):
        """
        Apply dashboard panel styling and selected-panel emphasis.
        """

        palette = palette_for_appearance_mode(
            getattr(self.app, "appearance_mode", None))
        selected = parameter == self.selected_parameter
        edgecolor = (
            palette["selected.edgecolor"]
            if selected
            else palette["axes.edgecolor"]
        )
        linewidth = 2.1 if selected else 1.0

        for spine in ax.spines.values():
            spine.set_color(edgecolor)
            spine.set_linewidth(linewidth)

    def __set_title(self):
        """
        Set a compact dashboard title with refresh status.
        """

        palette = palette_for_appearance_mode(
            getattr(self.app, "appearance_mode", None))
        if self.refresh_warning:
            subtitle = (
                "watching for file changes - refresh skipped: "
                f"{self.refresh_warning}"
            )
            color = palette["warning.color"]
        elif getattr(self.app, "auto_refresh", None) is not None and (
            not self.app.auto_refresh.get()
        ):
            subtitle = "auto-refresh paused - double-click a panel to focus"
            color = palette["subtle.text"]
        else:
            subtitle = "watching for file changes - double-click a panel to focus"
            color = palette["subtle.text"]

        self.figure.suptitle(
            "Simulation Monitor",
            x=0.012,
            y=0.985,
            ha="left",
            va="top",
            fontsize=scaled_font_size(
                14,
                self.__header_scale(1.5),
            ),
            fontweight="bold",
            color=palette["text.color"],
        )
        if self.subtitle_text is None:
            self.subtitle_text = self.figure.text(
                0.012,
                0.952,
                subtitle,
                ha="left",
                va="top",
                fontsize=scaled_font_size(
                    9,
                    self.__header_scale(1.25),
                ),
                color=color,
            )
        else:
            self.subtitle_text.set_text(subtitle)
            self.subtitle_text.set_color(color)
            self.subtitle_text.set_fontsize(
                scaled_font_size(
                    9,
                    self.__header_scale(1.25),
                ))

    def __set_window_title(self):
        """
        Name the native matplotlib window when the backend supports it.
        """

        manager = getattr(self.figure.canvas, "manager", None)
        if manager is not None and hasattr(manager, "set_window_title"):
            manager.set_window_title("PQEnalyzer - Live Monitor")
