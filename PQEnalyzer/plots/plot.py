"""
Base plotting workflow for GUI-backed matplotlib plots.
"""
import signal
from abc import abstractmethod, ABCMeta
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from .theme import apply_figure_theme, apply_matplotlib_theme


class Plot(metaclass=ABCMeta):
    """
    Shared lifecycle for time-series and histogram plot windows.

    Subclasses provide the concrete main-data, statistics and label rendering.
    This base class owns refresh/follow behavior and reads plot options from
    the active App instance before each render.

    Attributes
    ----------
    app : App
        The main application object.

    Methods
    -------
    simple(info_parameter)
        Render a static plot for the selected parameter.
    follow(info_parameter, interval)
        Refresh the plot at a fixed interval in seconds.
    refresh()
        Re-read the latest data and redraw an existing plot.
    """

    def __init__(self, app):
        """
        Initialize shared plot state and create the matplotlib axes.

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
        apply_matplotlib_theme(getattr(self.app, "appearance_mode", None))
        self.figure = plt.figure(figsize=(9, 5.5))
        self.ax = self.figure.add_subplot(111)
        self.apply_theme()

        # set the signal handler
        signal.signal(
            signal.SIGINT,
            lambda signal, frame: self.signal_handler(signal, frame),
        )

    def signal_handler(self, signal, frame):
        """
        Close plot and application windows after SIGINT.

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
        Copy the current plotting options from the App widgets.

        Returns
        -------
        None
        """

        self.mean = self.app.mean.get()
        self.median = self.app.median.get()
        self.cummulative_average = self.app.cummulative_average.get()
        self.self_correlation_mean = (
            self.app.self_correlation_mean.get())
        self.running_average = self.app.running_average.get()
        self.window_size = self.app.window_size.get()

        self.plot_main = self.app.plot_main_data.get()

        return None

    def simple(self, info_parameter: str) -> None:
        """
        Render a static plot for one info parameter.

        Main data is plotted unless the "No Data" option is selected. Enabled
        statistics are overlaid by the subclass implementation.

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
        Render a live plot and refresh it at the configured interval.

        Parameters
        ----------
        info_parameter : str
            The info parameter to plot.
        interval : int, optional
            The interval at which the plot is updated, in seconds.

        Returns
        -------
        None
        """

        self.info_parameter = info_parameter

        def update(frame):
            self.reader.read_last()
            self.ax.clear()
            self.apply_theme()
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
        Refresh an existing plot with the latest file contents and options.

        Returns
        -------
        None
        """

        # Reads the last data
        self.reader.read_last()

        self.redraw()

        # Show the plot
        plt.show()

    def redraw(self) -> None:
        """
        Redraw an existing plot without reading new file contents.
        """

        # Get the new parameters
        self.get_app_parameters()

        # Clear the plot
        self.ax.clear()
        self.apply_theme()

        # Plot the data
        self.plot_data()

        self.figure.canvas.draw_idle()

    def plot_data(self) -> None:
        """
        Render main data, enabled statistics and plot labels.

        Returns
        -------
        None
        """

        if not self.plot_main:
            self.main_data(self.info_parameter)

        self.statistics(self.info_parameter)

        self.labels(self.info_parameter)
        self.apply_theme()
        self.figure.tight_layout()

        return None

    def show_legend(self, **kwargs) -> bool:
        """
        Draw a consistently styled legend when plotted labels exist.
        """

        _, labels = self.ax.get_legend_handles_labels()
        if not labels:
            return False

        legend_options = {
            "fontsize": "small",
            "frameon": True,
        }
        legend_options.update(kwargs)
        self.ax.legend(**legend_options)
        return True

    def apply_theme(self) -> None:
        """
        Apply the active application appearance mode to this plot.
        """

        apply_figure_theme(
            self.figure,
            self.ax,
            getattr(self.app, "appearance_mode", None),
        )

    @abstractmethod
    def main_data(self, info_parameter: str):
        """
        Plot raw parameter data on the matplotlib axes.

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
        Set axis labels and legend for the plot.

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
        Plot enabled statistic overlays for the selected parameter.

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
