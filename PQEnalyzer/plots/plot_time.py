"""
Time-series plotting for PQ energy parameters.
"""

from ..energy_access import parameter_unit, series
from .._logging import get_logger
from .features import iter_time_series_overlays
from .labels import unique_path_labels
from .plot import Plot
from .value_readout import latest_value_label


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
            unit = parameter_unit(energy, info_parameter)
            self.ax.plot(
                energy_series.time,
                energy_series.values,
                label=latest_value_label(labels[i], energy_series.values,
                                         unit),
                linewidth=1.6,
                alpha=0.92,
                zorder=2,
            )

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

        if not self.show_legend(
            loc="best",
            fontsize="x-small",
            framealpha=0.82,
            borderpad=0.35,
            labelspacing=0.28,
            handlelength=1.8,
        ):
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
            unit = parameter_unit(self.reader.energies[0], info_parameter)
            for overlay in iter_time_series_overlays(
                self.reader.energies,
                info_parameter,
                self.options,
            ):
                self.ax.plot(
                    overlay.time,
                    overlay.values,
                    label=latest_value_label(overlay.label, overlay.values,
                                             unit),
                    **overlay.feature.matplotlib_style,
                )
        except ValueError as error:
            logger.warning("%s", error)

        return None
