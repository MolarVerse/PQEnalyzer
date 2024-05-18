import os

from .plot import Plot
from .statistic import Statistic


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
            basename = os.path.basename(self.reader.filenames[i])
            self.ax.plot(
                energy.simulation_time,
                energy.data[energy.info[info_parameter]],
                label=basename,
            )

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
                loc="upper center",
                bbox_to_anchor=(0.5, 1.15),
                ncol=5,
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

        if self.app.mean.get():
            # calculate mean and plot
            x, y = Statistic.mean(self.reader.energies, info_parameter)
            self.ax.plot(x, y, label="Mean", linestyle="--")

        if self.app.median.get():
            # calculate median and plot
            x, y = Statistic.median(self.reader.energies, info_parameter)
            self.ax.plot(x, y, label="Median", linestyle="--")

        if self.app.cummulative_average.get():
            # calculate cummulative average and plot
            x, y = Statistic.cummulative_average(self.reader.energies,
                                                 info_parameter)
            self.ax.plot(
                x,
                y,
                label="Cummulative Average",
                linestyle="--",
            )

        if self.app.auto_correlation.get():
            # calculate auto correlation and plot
            x, y = Statistic.auto_correlation(self.reader.energies,
                                              info_parameter)
            self.ax.plot(
                x,
                y,
                label="Auto Correlation",
                linestyle="--",
            )

        if self.app.running_average.get():
            # calculate running average and plot
            window_size = self.app.window_size.get()

            if window_size == "":
                window_size_int = 1000  # default window size
            else:
                window_size_int = int(window_size)

            x, y = Statistic.running_average(self.reader.energies,
                                             info_parameter, window_size_int)
            self.ax.plot(
                x,
                y,
                label="Running Average (" + str(window_size_int) + ")",
                linestyle="--",
            )

        return None
