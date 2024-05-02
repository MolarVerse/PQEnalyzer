import matplotlib.pyplot as plt
import os

from .plot import Plot
from .statistic import Statistic

class PlotTime(Plot):

    def __init__(self, app):

        super().__init__(app)
        
        return None
    
    def __main_data(self, info_parameter: str) -> None:
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

        for i, energy in enumerate(super.reader.energies):
            basename = os.path.basename(super.reader.filenames[i])
            super.ax.plot(
                energy.simulation_time,
                energy.data[energy.info[info_parameter]],
                label=basename,
            )

    
    def __labels(self, info_parameter: str) -> None:
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

        super.ax.set_xlabel("Simulation step")

        super.ax.set_ylabel(
            f"{info_parameter} / {super.reader.energies[0].units[info_parameter]}"
        )

        # legend outside of plot
        super.ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, 1.15),
            ncol=5,
            fancybox=True,
            shadow=True,
        )

        return None

    def __statistics(self, info_parameter: str) -> None:
        """
        Plot the statistics of the data on the plot frame.

        Parameters
        ----------
        info_parameter : str
            The info parameter to calculate the statistics of.

        Returns
        -------
        None
        """
        if super.app.mean.get():
            # calculate mean and plot
            x, y = Statistic.mean(super.reader.energies, info_parameter)
            super.ax.plot(x, y, label="Mean", linestyle="--")

        if super.app.median.get():
            # calculate median and plot
            x, y = Statistic.median(super.reader.energies, info_parameter)
            super.ax.plot(x, y, label="Median", linestyle="--")

        if super.app.cummulative_average.get():
            # calculate cummulative average and plot
            x, y = Statistic.cummulative_average(super.reader.energies, info_parameter)
            super.ax.plot(
                x,
                y,
                label="Cummulative Average",
                linestyle="--",
            )

        if super.app.auto_correlation.get():
            # calculate auto correlation and plot
            x, y = Statistic.auto_correlation(super.reader.energies, info_parameter)
            super.ax.plot(
                x,
                y,
                label="Auto Correlation",
                linestyle="--",
            )

        if super.app.running_average.get():
            # calculate running average and plot
            window_size = super.app.window_size.get()

            if window_size == "":
                window_size_int = 1000  # default window size
            else:
                window_size_int = int(window_size)

            x, y = Statistic.running_average(
                super.reader.energies, info_parameter, window_size_int
            )
            super.ax.plot(
                x,
                y,
                label="Running Average (" + str(window_size_int) + ")",
                linestyle="--",
            )

        return None
