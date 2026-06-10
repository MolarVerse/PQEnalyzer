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
from .theme import apply_figure_theme, apply_matplotlib_theme


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

        apply_matplotlib_theme(getattr(self.app, "appearance_mode", None))
        self.figure = plt.figure(figsize=self.__figure_size())
        self.axes = self.__create_axes()
        self.ani = None

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

        if self.__safe_read_last():
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

        for ax in self.axes[len(self.parameters):]:
            ax.set_visible(False)

        self.__show_legend()
        self.figure.suptitle("Simulation Dashboard")
        self.figure.tight_layout(rect=(0, 0, 1, 0.96))
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
            )
            self.__add_latest_value(ax, energy_series.time,
                                    energy_series.values)

    def __label_axis(self, ax, parameter, index):
        """
        Label one dashboard axis compactly.
        """

        unit = parameter_unit(self.reader.energies[0], parameter)
        ax.set_title(f"{parameter} / {unit}", fontsize=9)
        ax.ticklabel_format(axis="both", style="sci")
        ax.tick_params(labelsize=8)

        ncols = self.__grid_shape()[1]
        if index >= len(self.axes) - ncols:
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
            fontsize=6,
            horizontalalignment="left",
            verticalalignment="center",
            bbox=dict(facecolor="white", alpha=0.45, edgecolor="white"),
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
                    loc="upper center",
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
            logger.warning("Dashboard refresh skipped: %s", error)
            return False

        return True

    def __button_press_event(self, event):
        """
        Open a focused plot when a dashboard panel is double-clicked.
        """

        if not getattr(event, "dblclick", False):
            return

        parameter = self.axis_parameters.get(event.inaxes)
        if parameter is None:
            return

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
