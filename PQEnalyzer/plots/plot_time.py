"""
Time-series plotting for PQ energy parameters.
"""

from ..statistics import Statistic
from ..energy_access import (
    concatenate_series,
    difference_series,
    series,
)
from .._logging import get_logger
from .labels import unique_path_labels
from .plot import Plot


logger = get_logger(__name__)


class PlotTime(Plot):
    """
    Plot selected energy parameters against simulation time.

    Attributes
    ----------
    app : App
        The main application object.
    """

    def __init__(self, app):
        """
        Initialize a time-series plot window.

        Parameters
        ----------
        app : App
            The main application object.

        Returns
        -------
        None
        """

        super().__init__(app)

        return None

    def main_data(self, info_parameter: str) -> None:
        """
        Plot each input file as a separate time-series line.

        Parameters
        ----------
        info_parameter : str
            The info parameter to plot.

        Returns
        -------
        None
        """

        labels = unique_path_labels(self.reader.filenames)
        for i, energy in enumerate(self.reader.energies):
            energy_series = series(energy, info_parameter)
            self.ax.plot(
                energy_series.time,
                energy_series.values,
                label=labels[i],
                linewidth=1.6,
                alpha=0.92,
                zorder=2,
            )
            self.add_value_label(energy_series.time, energy_series.values)

    def labels(self, info_parameter: str) -> None:
        """
        Set time-series labels and legend.

        Parameters
        ----------
        info_parameter : str
            The info parameter to set the labels of the plot frame.

        Returns
        -------
        None
        """

        self.style_single_plot(
            title=f"{info_parameter} time series",
            xlabel="Simulation step",
            ylabel=self.parameter_axis_label(info_parameter),
        )

        if not self.show_legend(loc="best"):
            logger.warning("No data to plot.")

        return None

    def statistics(self, info_parameter: str) -> None:
        """
        Plot enabled statistic overlays for the selected time series.

        Parameters
        ----------
        info_parameter : str
            The info parameter to calculate the statistics of.

        Returns
        -------
        None
        """

        if self.difference:
            try:
                delta_series = difference_series(
                    self.reader.energies, info_parameter)
            except ValueError as error:
                logger.warning("%s", error)
            else:
                self.ax.plot(
                    delta_series.time,
                    delta_series.values,
                    label="Difference (1 - 2)",
                    linestyle="-",
                    linewidth=1.9,
                    alpha=0.95,
                    zorder=4,
                )
                self.add_value_label(delta_series.time, delta_series.values)

            return None

        energy_series = concatenate_series(self.reader.energies,
                                           info_parameter)

        if self.mean:
            # calculate mean and plot
            x, y = Statistic.mean_values(energy_series.time,
                                         energy_series.values)
            self.ax.plot(
                x,
                y,
                label="Mean",
                linestyle="--",
                linewidth=1.15,
                alpha=0.85,
                zorder=3,
            )

            self.add_value_label(x, y)

        if self.median:
            # calculate median and plot
            x, y = Statistic.median_values(energy_series.time,
                                           energy_series.values)
            self.ax.plot(
                x,
                y,
                label="Median",
                linestyle=":",
                linewidth=1.35,
                alpha=0.9,
                zorder=3,
            )

            self.add_value_label(x, y)

        if self.cummulative_average:
            # calculate cumulative average and plot
            x, y = Statistic.cumulative_average_values(
                energy_series.time, energy_series.values)
            self.ax.plot(
                x,
                y,
                label="Cumulative Average",
                linestyle="-.",
                linewidth=1.45,
                alpha=0.9,
                zorder=3,
            )

            self.add_value_label(x, y)

        if self.self_correlation_mean:
            x, y = Statistic.self_correlation_mean_values(
                energy_series.time, energy_series.values)
            self.ax.plot(
                x,
                y,
                label="Self-Correlation Mean",
                linestyle=(0, (2, 2)),
                linewidth=1.45,
                alpha=0.9,
                zorder=3,
            )

            self.add_value_label(x, y)

        if self.running_average:
            # calculate running average and plot
            try:
                window_size_int = self.__parse_window_size(self.window_size)
                x, y = Statistic.running_average_values(
                    energy_series.time,
                    energy_series.values,
                    window_size_int,
                )
            except ValueError as error:
                logger.warning("%s", error)
                return None

            self.ax.plot(
                x,
                y,
                label="Running Average (" + str(window_size_int) + ")",
                linestyle="-",
                linewidth=2.0,
                alpha=0.95,
                zorder=4,
            )

            self.add_value_label(x, y)

        return None

    def __parse_window_size(self, window_size):
        """
        Parse the running-average window size from a GUI entry string.
        """
        stripped_window_size = window_size.strip()

        if stripped_window_size in {"", "."}:
            return 1000

        parsed_window_size = int(float(stripped_window_size))
        if parsed_window_size < 1:
            raise ValueError("Window size must be positive")

        return parsed_window_size

    def add_value_label(self, x, y) -> None:
        """
        Add a value label for the last y point.

        Parameters
        ----------
        x : float
            The x coordinate of the value label.
        y : float
            The y coordinate of the value label.

        Returns
        -------
        None
        """

        self.ax.annotate(
            f"{y[-1]:.3e}",
            xy=(x[-1], y[-1]),
            xytext=(6, 0),
            textcoords="offset points",
            fontsize=8,
            horizontalalignment="left",
            verticalalignment="center",
            bbox=self.annotation_box(),
            zorder=5,
        )

        return None
