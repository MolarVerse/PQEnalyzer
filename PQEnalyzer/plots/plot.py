"""
The plot module contains the Plot class for the PQEnalyzer application.
"""
import signal
from abc import abstractmethod, ABCMeta
import matplotlib.pyplot as plt


class Plot(metaclass=ABCMeta):
    """
    The plot class for the PQEnalyzer application.

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

        # read parameters from the app
        self.get_app_parameters()

        # create the plot frame
        self.plot_frame = plt.figure()
        self.ax = self.plot_frame.add_subplot(111)
        self.plot_frame.show()

    def get_app_parameters(self):
        """
        Get the parameter from the app.

        Returns
        -------
        None
        """

        self.mean = self.app.mean.get()
        self.median = self.app.median.get()
        self.cummulative_average = self.app.cummulative_average.get()
        self.auto_correlation = self.app.auto_correlation.get()
        self.running_average = self.app.running_average.get()
        self.window_size = self.app.window_size.get()

        self.plot_main = self.app.plot_main_data.get()

        return None

    def display(self, info_parameter: str) -> None:
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
        if not self.plot_main:
            self.main_data(info_parameter)

        self.statistics(info_parameter)

        self.labels(info_parameter)

    def follow(self, info_parameter: str, interval: int = 1000) -> None:
        """
        Plot the live data. Clears the plot and replots the data at a given interval.
        Exits the plot if the window is closed.

        Parameters
        ----------
        info_parameter : str
            The info parameter to plot.
        interval : int, optional
            The interval at which the plot is updated in milliseconds. Default is 1000.

        Returns
        -------
        None
        """

        while True:
            self.updatePlot(info_parameter)

            if self.plot_frame.number not in plt.get_fignums():
                break

            if signal.getsignal(signal.SIGINT):
                break

            # sleep for interval
            plt.pause(interval / 1000)

    def refresh(self, info_parameter: str) -> None:
        """
        Refresh the plot. Clears the plot, gets the new parameters
        and plots the data again.

        Parameters
        ----------
        info_parameter : str
            The info parameter to plot.

        Returns
        -------
        None
        """

        self.get_app_parameters()
        self.updatePlot(info_parameter)

    def updatePlot(self, info_parameter: str) -> None:
        """
        Refresh the plot. Clears the plot, gets the new parameters
        and plots the data again.

        Parameters
        ----------
        info_parameter : str
            The info parameter to plot.

        Raises
        ------
        Exception
            If the reader cannot read the last file. 

        Returns
        -------
        None
        """

        try:
            self.reader.read_last()
        except Exception as e:
            raise e

        self.ax.clear()

        self.display(info_parameter)

    @abstractmethod
    def main_data(self, info_parameter: str):
        """
        Plot the main data on the plot frame.

        Parameters
        ----------
        info_parameter : str
            The info parameter to plot.

        Raises
        ------
        NotImplementedError
            If the method is not implemented in the subclass.
        """
        raise NotImplementedError

    @abstractmethod
    def labels(self, info_parameter: str):
        """
        Set the labels of the plot frame using the info parameter.

        Parameters
        ----------
        info_parameter : str
            The info parameter to set the labels of the plot frame.

        Raises
        ------
        NotImplementedError
            If the method is not implemented in the subclass.
        """
        raise NotImplementedError

    @abstractmethod
    def statistics(self, info_parameter: str):
        """
        Plot the statistics of the data on the plot frame.

        Parameters
        ----------
        info_parameter : str
            The info parameter to calculate the statistics of.

        Raises
        ------
        NotImplementedError
            If the method is not implemented in the subclass.
        """
        raise NotImplementedError
