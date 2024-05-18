import matplotlib.pyplot as plt
from abc import abstractmethod, ABCMeta


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
            self.main_data(info_parameter)

        self.statistics(info_parameter)

        self.labels(info_parameter)

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
            The interval which the plot is updated in milliseconds.

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
            plt.pause(interval / 1000)

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
