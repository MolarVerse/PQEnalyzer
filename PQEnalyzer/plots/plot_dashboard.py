"""
Live dashboard plotting for all available time-series parameters.
"""

import math
import signal

import matplotlib.animation as animation
import matplotlib.pyplot as plt

from .._logging import get_logger
from ..energy_access import parameter_unit, series
from .labels import unique_path_labels
from .theme import (
    apply_figure_theme,
    apply_matplotlib_theme,
    palette_for_appearance_mode,
)


logger = get_logger(__name__)


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
        self.selected_parameter = None
        self.refresh_warning = None
        self.subtitle_text = None

        apply_matplotlib_theme(getattr(self.app, "appearance_mode", None))
        self.figure = plt.figure(figsize=self.__figure_size())
        self.axes = self.__create_axes()
        self.ani = None
        self.__set_window_title()

        signal.signal(
            signal.SIGINT,
            lambda signal, frame: self.signal_handler(signal, frame),
        )
        self.figure.canvas.mpl_connect("button_press_event",
                                       self.__button_press_event)

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
        self.ani = animation.FuncAnimation(
            self.figure,
            update,
            blit=True,
            interval=interval * 1000,
            cache_frame_data=False,
        )
        plt.show()

    def refresh(self) -> None:
        """
        Refresh the dashboard while keeping the previous view on read errors.
        """

        if not self.__safe_read_last():
            self.__set_title()
            self.figure.canvas.draw_idle()
            return None

        self.redraw()
        plt.show()

    def redraw(self) -> None:
        """
        Redraw all raw parameter panels.
        """

        for ax in self.axes:
            ax.clear()
            apply_figure_theme(
                self.figure,
                ax,
                getattr(self.app, "appearance_mode", None),
            )

        self.axis_parameters = {}
        labels = unique_path_labels(self.reader.filenames)

        for index, parameter in enumerate(self.parameters):
            ax = self.axes[index]
            self.axis_parameters[ax] = parameter
            self.__plot_parameter(ax, parameter, labels)
            self.__label_axis(ax, parameter, index)
            self.__style_axis(ax, parameter)

        for ax in self.axes[len(self.parameters):]:
            ax.set_visible(False)

        self.__show_legend()
        self.__set_title()
        self.figure.tight_layout(rect=(0, 0.03, 1, 0.91), h_pad=1.0)
        self.figure.canvas.draw_idle()

    def __plot_parameter(self, ax, parameter, labels):
        """
        Plot one raw parameter panel.
        """

        for index, energy in enumerate(self.reader.energies):
            energy_series = series(energy, parameter)
            ax.plot(
                energy_series.time,
                energy_series.values,
                label=labels[index],
                linewidth=1.45,
                alpha=0.92,
            )
            self.__add_latest_value(ax, energy_series.time,
                                    energy_series.values)

    def __label_axis(self, ax, parameter, index):
        """
        Label one dashboard axis compactly.
        """

        unit = parameter_unit(self.reader.energies[0], parameter)
        ax.set_title(f"{parameter} / {unit}", fontsize=9, loc="left", pad=6)
        ax.ticklabel_format(axis="both", style="sci")
        ax.tick_params(labelsize=8)

        nrows, ncols = self.__grid_shape()
        if index // ncols == nrows - 1:
            ax.set_xlabel("Simulation step", fontsize=8)

    def __add_latest_value(self, ax, x, y):
        """
        Add a compact latest-value label to one dashboard line.
        """

        if len(x) == 0 or len(y) == 0:
            return

        ax.annotate(
            f"{y[-1]:.3e}",
            xy=(x[-1], y[-1]),
            xytext=(4, 0),
            textcoords="offset points",
            fontsize=6.5,
            horizontalalignment="left",
            verticalalignment="center",
            bbox=dict(boxstyle="round,pad=0.18",
                      facecolor="white",
                      alpha=0.5,
                      edgecolor="white"),
        )

    def __show_legend(self):
        """
        Draw one shared legend for the dashboard.
        """

        for ax in self.axes:
            handles, labels = ax.get_legend_handles_labels()
            if labels:
                self.figure.legend(
                    handles,
                    labels,
                    loc="upper right",
                    bbox_to_anchor=(0.995, 0.995),
                    ncol=min(4, len(labels)),
                    fontsize="small",
                    frameon=True,
                )
                return

        logger.warning("No data to plot.")

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

    def __create_axes(self):
        """
        Create enough axes for all dashboard parameters.
        """

        nrows, ncols = self.__grid_shape()
        axes = self.figure.subplots(nrows=nrows, ncols=ncols, squeeze=False)
        return list(axes.flat)

    def __grid_shape(self):
        """
        Return a compact dashboard grid shape.
        """

        number_of_parameters = max(1, len(self.parameters))
        ncols = min(3, math.ceil(math.sqrt(number_of_parameters)))
        nrows = math.ceil(number_of_parameters / ncols)
        return nrows, ncols

    def __figure_size(self):
        """
        Return a readable figure size for the current parameter count.
        """

        nrows, ncols = self.__grid_shape()
        return (4.4 * ncols, 2.8 * nrows)

    def __style_axis(self, ax, parameter):
        """
        Apply dashboard panel styling and selected-panel emphasis.
        """

        palette = apply_figure_theme(
            self.figure,
            ax,
            getattr(self.app, "appearance_mode", None),
        )
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
            subtitle = f"raw live monitor - refresh skipped: {self.refresh_warning}"
            color = palette["warning.color"]
        else:
            subtitle = "raw live monitor - double-click a panel to focus"
            color = palette["subtle.text"]

        self.figure.suptitle(
            "Simulation Dashboard",
            x=0.012,
            y=0.995,
            ha="left",
            va="top",
            fontsize=14,
            fontweight="bold",
            color=palette["text.color"],
        )
        if self.subtitle_text is None:
            self.subtitle_text = self.figure.text(
                0.012,
                0.955,
                subtitle,
                ha="left",
                va="top",
                fontsize=9,
                color=color,
            )
        else:
            self.subtitle_text.set_text(subtitle)
            self.subtitle_text.set_color(color)

    def __set_window_title(self):
        """
        Name the native matplotlib window when the backend supports it.
        """

        manager = getattr(self.figure.canvas, "manager", None)
        if manager is not None and hasattr(manager, "set_window_title"):
            manager.set_window_title("PQEnalyzer Dashboard")
