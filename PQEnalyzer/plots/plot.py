"""
The plot module contains the Plot class for the PQEnalyzer application.
"""
import signal
from abc import abstractmethod, ABCMeta
import matplotlib.pyplot as plt
import matplotlib.animation as animation


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

        # create the plot
        self.figure = plt.figure()
        self.ax = self.figure.add_subplot(111)

        # set the signal handler
        signal.signal(
            signal.SIGINT,
            lambda signal, frame: self.signal_handler(signal, frame),
        )

    def signal_handler(self, signal, frame):
        """
        Close the plot window when the signal is received.

        Parameters
        ----------
        signal : int
            The signal to handle.
        frame : int
            The frame to handle.

        Returns
        -------
        None
        """

        plt.close("all")
        self.app.destroy()

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

    def simple(self, info_parameter: str) -> None:
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

        self.info_parameter = info_parameter

        # if button is not checked, plot main data
        self.plot_data()

        plt.show()

    def follow(self, info_parameter: str, interval: float = 1.0) -> None:
        """
        Plot the live data. Clears the plot and replots the data at a given interval.
        Exits the plot if the window is closed.

        Parameters
        ----------
        info_parameter : str
            The info parameter to plot.
        interval : int, optional
            The interval at which the plot is updated in seconds

        Returns
        -------
        None
        """

        self.info_parameter = info_parameter

        def update(frame):
            self.reader.read_last()
            self.ax.clear()
            self.plot_data()
            return []

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

        # Reads the last data
        self.reader.read_last()

        # Get the new parameters
        self.get_app_parameters()

        # Clear the plot
        self.ax.clear()

        # Plot the data
        self.plot_data()

        # Show the plot
        plt.show()

    def plot_data(self) -> None:
        """
        Plot the data.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        if not self.plot_main:
            self.main_data(self.info_parameter)

        self.statistics(self.info_parameter)

        self.labels(self.info_parameter)

        return None

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
