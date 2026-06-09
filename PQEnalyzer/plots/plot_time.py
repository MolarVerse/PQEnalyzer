"""
Time-series plotting for PQ energy parameters.
"""

from ..statistics import Statistic
from ..energy_access import concatenate_series, parameter_unit, series
from .._logging import get_logger
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

        for i, energy in enumerate(self.reader.energies):
            energy_series = series(energy, info_parameter)
            self.ax.plot(
                energy_series.time,
                energy_series.values,
                label=self.reader.filenames[i],
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

        self.ax.set_xlabel("Simulation step")

        self.ax.ticklabel_format(axis="both", style="sci")

        self.ax.set_ylabel(
            f"{info_parameter} / "
            f"{parameter_unit(self.reader.energies[0], info_parameter)}"
        )

        # Check if label is empty
        if self.ax.get_legend_handles_labels()[1] == []:
            logger.warning("No data to plot.")
        else:
            # legend outside of plot
            self.ax.legend(
                fontsize="small",
                fancybox=True,
                shadow=True,
            )

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

        energy_series = concatenate_series(self.reader.energies,
                                           info_parameter)

        if self.mean:
            # calculate mean and plot
            x, y = Statistic.mean_values(energy_series.time,
                                         energy_series.values)
            self.ax.plot(x, y, label="Mean", linestyle="--")

            self.add_value_label(x, y)

        if self.median:
            # calculate median and plot
            x, y = Statistic.median_values(energy_series.time,
                                           energy_series.values)
            self.ax.plot(x, y, label="Median", linestyle="--")

            self.add_value_label(x, y)

        if self.cummulative_average:
            # calculate cumulative average and plot
            x, y = Statistic.cumulative_average_values(
                energy_series.time, energy_series.values)
            self.ax.plot(
                x,
                y,
                label="Cumulative Average",
                linestyle="--",
            )

            self.add_value_label(x, y)

        if self.auto_correlation:
            # calculate auto correlation and plot
            x, y = Statistic.auto_correlation_values(energy_series.time,
                                                     energy_series.values)
            self.ax.plot(
                x,
                y,
                label="Auto Correlation",
                linestyle="--",
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
                linestyle="--",
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

        self.ax.text(
            self.ax.get_xlim()[1],
            y[-1],
            f"{y[-1]:.3e}",
            fontsize=8,
            horizontalalignment="left",
            bbox=dict(facecolor="white", alpha=0.5, edgecolor="white"),
        )

        return None
