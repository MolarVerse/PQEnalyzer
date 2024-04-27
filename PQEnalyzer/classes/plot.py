import matplotlib.pyplot as plt
import numpy as np
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
    """

    def __init__(self, app):
        """
        Constructs all the necessary attributes for the Plot object.

        Parameters
        ----------
        app : App
            The main application object.
        """

        self.app = app
        self.reader = app.reader

    def build_plot(self):
        """
        Build the plot.
        """

        self.plot_frame = plt.figure()
        self.ax = self.plot_frame.add_subplot(111)

    def plot(self, info_parameter: str) -> None:
        """
        Plot the data.
        """
        # if button is not checked, plot main data
        if not self.app.plot_main_data.get():
            for i, energy in enumerate(self.reader.energies):
                basename = os.path.basename(self.reader.filenames[i])
                self.ax.plot(
                    energy.simulation_time,
                    energy.data[energy.info[info_parameter]],
                    label=basename,
                )

        self.__statistics(info_parameter)

        # TODO: implement steps to ps time conversion
        # self.ax.set_xlabel(f'Simulation time / {self.reader.energies[0].units["SIMULATION-TIME"]}')
        
        self.ax.set_xlabel(f"Simulation step")
        
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
        self.plot_frame.show()

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
                window_size_int = 100  # default window size
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
