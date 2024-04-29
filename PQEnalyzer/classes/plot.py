import matplotlib.pyplot as plt
import os

from .statistic import Statistic

class Plot:
    """
    The plot class for the PQEnalyzer application.

    ...

    Attributes
    ----------
    app : App
        The main application object.

    Methods
    -------
    build_plot()
        Build the plot.
    plot(info_parameter)
        Plot the data.

    Examples
    --------
    >>> plot = Plot(app)
    >>> plot.build_plot()
    >>> plot.plot("ENERGY")
    >>> plot.live_plot("ENERGY", 1)
    """

    def __init__(self, app):
        """
        Constructs all the necessary attributes for the Plot object.

        Parameters
        ----------
        app : App
            The main application object.

        Returns
        -------
        None
        """

        self.app = app
        self.reader = app.reader

        return None

    def build_plot(self):
        """
        Build the plot. Creates a plot frame and an axis.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        self.plot_frame = plt.figure()
        self.ax = self.plot_frame.add_subplot(111)
        self.plot_frame.show()

        return None

    def plot(self, info_parameter: str) -> None:
        """
        Plot the data. If the button is not checked, plot the main data.
        Checks if the statistics buttons are checked and plots the statistics, too.

        Parameters
        ----------
        info_parameter : str
            The info parameter to plot.

        Returns
        -------
        None
        """

        # if button is not checked, plot main data
        if not self.app.plot_main_data.get():
            self.__main_data(info_parameter)

        self.__statistics(info_parameter)

        self.__labels(info_parameter)

        return None

    def live_plot(self, info_parameter: str, interval: int = 1000) -> None:
        """
        Plot the live data. Clears the plot and replots the data at a given interval.
        Exits the plot if the window is closed.

        Parameters
        ----------
        info_parameter : str
            The info parameter to plot.
        interval : int
            The interval which the plot is updated.

        Returns
        -------
        None
        """

        while True:
            # clear the plot
            self.ax.clear()
            self.reader.read_last()

            self.plot(info_parameter)

            # sleep for interval
            plt.pause(interval)

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

        for i, energy in enumerate(self.reader.energies):
            basename = os.path.basename(self.reader.filenames[i])
            self.ax.plot(
                energy.simulation_time,
                energy.data[energy.info[info_parameter]],
                label=basename,
            )

        return None
    
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

        self.ax.set_xlabel("Simulation step")

        self.ax.set_ylabel(
            f"{info_parameter} / {self.reader.energies[0].units[info_parameter]}"
        )

        # legend outside of plot
        self.ax.legend(
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
            x, y = Statistic.cummulative_average(self.reader.energies, info_parameter)
            self.ax.plot(
                x,
                y,
                label="Cummulative Average",
                linestyle="--",
            )

        if self.app.auto_correlation.get():
            # calculate auto correlation and plot
            x, y = Statistic.auto_correlation(self.reader.energies, info_parameter)
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

            x, y = Statistic.running_average(
                self.reader.energies, info_parameter, window_size_int
            )
            self.ax.plot(
                x,
                y,
                label="Running Average (" + str(window_size_int) + ")",
                linestyle="--",
            )

        return None
