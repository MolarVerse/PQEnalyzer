"""
The plot the parameters dependent on the simulation time
for the PQEnalyzer application.
"""

import os
import numpy as np

from ..statistics import Statistic
from .plot import Plot


class PlotTime(Plot):
    """
    The plot the parameters dependent on the simulation time
    for the PQEnalyzer application.

    ...

    Attributes
    ----------
    app : App
        The main application object.
    
    Methods
    -------
    plot(info_parameter)
        Plot the data.
    live_plot(info_parameter, interval)
        Plot the live data at a given interval in milliseconds.
    """

    def __init__(self, app):
        """
        Constructs all the necessary attributes for the PlotTime object.

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
        Plot the main data on the plot frame.

        Parameters
        ----------
        info_parameter : str
            The info parameter to plot.

        Returns
        -------
        None
        """

        for i, energy in enumerate(self.reader.energies):
            self.ax.plot(
                energy.simulation_time,
                energy.data[energy.info[info_parameter]],
                label=self.reader.filenames[i],
            )
        self.add_value_label(energy.simulation_time, energy.data[energy.info[info_parameter]])

    def labels(self, info_parameter: str) -> None:
        """
        Set the labels of the plot frame using the info parameter.

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
            f"{info_parameter} / {self.reader.energies[0].units[info_parameter]}"
        )

        # Check if label is empty
        if self.ax.get_legend_handles_labels()[1] == []:
            # raise warning if no data to plot
            # TODO: change to logger
            # raise RuntimeWarning("No data to plot.")
            print("No data to plot.")
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
        Plot the statistics of the data dependent on the simulation time
        to the plot frame using the info parameter.

        Parameters
        ----------
        info_parameter : str
            The info parameter to calculate the statistics of.

        Returns
        -------
        None
        """

        if self.mean:
            # calculate mean and plot
            x, y = Statistic.mean(self.reader.energies, info_parameter)
            self.ax.plot(x, y, label="Mean", linestyle="--")

            self.add_value_label(x, y)

        if self.median:
            # calculate median and plot
            x, y = Statistic.median(self.reader.energies, info_parameter)
            self.ax.plot(x, y, label="Median", linestyle="--")

            self.add_value_label(x, y)

        if self.cummulative_average:
            # calculate cummulative average and plot
            x, y = Statistic.cummulative_average(self.reader.energies,
                                                 info_parameter)
            self.ax.plot(
                x,
                y,
                label="Cummulative Average",
                linestyle="--",
            )

            self.add_value_label(x, y)

        if self.auto_correlation:
            # calculate auto correlation and plot
            x, y = Statistic.auto_correlation(self.reader.energies,
                                              info_parameter)
            self.ax.plot(
                x,
                y,
                label="Auto Correlation",
                linestyle="--",
            )

            self.add_value_label(x, y)

        if self.running_average:
            # calculate running average and plot
            window_size = self.window_size

            if window_size == "":
                window_size_int = 1000  # default window size
            else:
                window_size_int = int(float(window_size))

            try:
                x, y = Statistic.running_average(self.reader.energies,
                                             info_parameter, window_size_int)
            except ValueError:
                # raise warning if window size is too large
                print("Window size is too large.")
                return None
                
            self.ax.plot(
                x,
                y,
                label="Running Average (" + str(window_size_int) + ")",
                linestyle="--",
            )

            self.add_value_label(x, y)

        return None

    def add_value_label(self, x, y) -> None:
        """
        Add a value label of the last y point to the plot frame.

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
