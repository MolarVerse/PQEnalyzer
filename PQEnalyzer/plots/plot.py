"""
Base plotting workflow for GUI-backed matplotlib plots.
"""
import signal
from abc import abstractmethod, ABCMeta
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from ..energy_access import parameter_unit
from .._logging import get_logger
from .features import PLOT_FEATURES
from .options import PlotOptions
from .theme import apply_figure_theme, apply_matplotlib_theme


logger = get_logger(__name__)


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
        self.options = PlotOptions.from_app(app)

        # read parameters from the app
        self.get_app_parameters()

        # create the plot
        self.palette = apply_matplotlib_theme(
            getattr(self.app, "appearance_mode", None))
        self.figure = plt.figure(figsize=(9, 5.5))
        self.ax = self.figure.add_subplot(111)
        self.apply_theme()
        self.figure.canvas.mpl_connect("button_press_event",
                                       self.__select_plot)

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

        for feature in PLOT_FEATURES:
            setattr(
                self,
                feature.option_attribute,
                getattr(self.options, feature.option_attribute),
            )
        self.window_size = self.options.window_size

        self.plot_main = self.options.plot_main

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
        self.app.select_plot(self)

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
        self.app.select_plot(self)

        def update(frame):
            try:
                self.reader.read_last()
            except Exception as error:  # pylint: disable=broad-exception-caught
                logger.warning("Plot refresh skipped: %s", error)
                return []

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

    def refresh(self, show=True) -> None:
        """
        Refresh an existing plot with the latest file contents and options.

        Returns
        -------
        None
        """

        try:
            self.reader.read_last()
        except Exception as error:  # pylint: disable=broad-exception-caught
            logger.warning("Plot refresh skipped: %s", error)
            return None

        self.redraw()

        # Show the plot
        if show:
            plt.show()

    def redraw(self, options=None) -> None:
        """
        Redraw an existing plot without reading new file contents.
        """

        if options is not None:
            self.options = options

        # Get the new parameters
        self.get_app_parameters()

        # Clear the plot
        self.ax.clear()
        self.apply_theme()

        # Plot the data
        self.plot_data()

        self.figure.canvas.draw_idle()

    def __select_plot(self, event):
        """
        Select this plot so GUI controls edit its options.
        """

        if getattr(event, "inaxes", None) is not self.ax:
            return

        self.app.select_plot(self)

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
        self.figure.tight_layout(pad=2.0)

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

    def parameter_axis_label(self, info_parameter: str) -> str:
        """
        Return a parameter label including the reader-reported unit.
        """

        unit = parameter_unit(self.reader.energies[0], info_parameter)
        return f"{info_parameter} / {unit}"

    def style_single_plot(
        self,
        *,
        title: str,
        xlabel: str,
        ylabel: str,
    ) -> None:
        """
        Apply shared single-plot labels and framing.
        """

        self.set_window_title(title)
        self.ax.set_title(title, loc="left", pad=10)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.ticklabel_format(axis="both", style="sci")
        self.ax.margins(x=0.02, y=0.08)

    def set_window_title(self, title: str) -> None:
        """
        Name the native matplotlib window when the backend supports it.
        """

        manager = getattr(self.figure.canvas, "manager", None)
        if manager is not None and hasattr(manager, "set_window_title"):
            manager.set_window_title(f"PQEnalyzer - {title}")

    def apply_theme(self) -> None:
        """
        Apply the active application appearance mode to this plot.
        """

        self.palette = apply_figure_theme(
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
