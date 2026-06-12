"""
Time-series plotting for PQ energy parameters.
"""

from ..energy_access import series
from .._logging import get_logger
from .features import iter_time_series_overlays
from .labels import unique_path_labels
from .plot import Plot


logger = get_logger(__name__)


class PlotTime(Plot):
    """
    Plot selected energy parameters against simulation time.

    Attributes
    ----------
    app : App
        The main application object.
    """

    def __init__(self, app):
        """
        Initialize a time-series plot window.

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
        Plot each input file as a separate time-series line.

        Parameters
        ----------
        info_parameter : str
            The info parameter to plot.

        Returns
        -------
        None
        """

        labels = unique_path_labels(self.reader.filenames)
        for i, energy in enumerate(self.reader.energies):
            energy_series = series(energy, info_parameter)
            self.ax.plot(
                energy_series.time,
                energy_series.values,
                label=labels[i],
                linewidth=1.6,
                alpha=0.92,
                zorder=2,
            )
            self.add_value_label(energy_series.time, energy_series.values)

    def labels(self, info_parameter: str) -> None:
        """
        Set time-series labels and legend.

        Parameters
        ----------
        info_parameter : str
            The info parameter to set the labels of the plot frame.

        Returns
        -------
        None
        """

        self.style_single_plot(
            title=f"{info_parameter} time series",
            xlabel="Simulation step",
            ylabel=self.parameter_axis_label(info_parameter),
        )

        if not self.show_legend(loc="best"):
            logger.warning("No data to plot.")

        return None

    def statistics(self, info_parameter: str) -> None:
        """
        Plot enabled statistic overlays for the selected time series.

        Parameters
        ----------
        info_parameter : str
            The info parameter to calculate the statistics of.

        Returns
        -------
        None
        """

        try:
            for overlay in iter_time_series_overlays(
                self.reader.energies,
                info_parameter,
                self.options,
            ):
                self.ax.plot(
                    overlay.time,
                    overlay.values,
                    label=overlay.label,
                    **overlay.feature.matplotlib_style,
                )
                self.add_value_label(overlay.time, overlay.values)
        except ValueError as error:
            logger.warning("%s", error)

        return None

    def add_value_label(self, x, y) -> None:
        """
        Add a value label for the last y point.

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

        self.ax.annotate(
            f"{y[-1]:.3e}",
            xy=(x[-1], y[-1]),
            xytext=(6, 0),
            textcoords="offset points",
            fontsize=8,
            horizontalalignment="left",
            verticalalignment="center",
            bbox=self.annotation_box(),
            zorder=5,
        )

        return None
