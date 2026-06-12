"""
Histogram/KDE plotting for PQ energy parameters.
"""
from scipy.stats import gaussian_kde
import numpy as np

from ..energy_access import parameter_values
from .._logging import get_logger
from .features import iter_histogram_guides
from .labels import unique_path_labels
from .plot import Plot


logger = get_logger(__name__)


class PlotHistogram(Plot):
    """
    Plot kernel-density estimates for selected energy parameters.

    Attributes
    ----------
    app : App
        The main application object.

    """

    def __init__(self, app):
        """
        Initialize a histogram plot window.

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
        Plot one KDE curve per input file.

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
            data = parameter_values(energy, info_parameter)

            # check if zero data
            if np.unique(data).size == 1:
                logger.warning("Data zero. No histogram available.")
                continue

            # plot kde of histogram
            kde = gaussian_kde(data)

            x = np.linspace(
                min(data),
                max(data),
                1000,
            )

            y = kde(x)
            line = self.ax.plot(
                x,
                y,
                label=f"{labels[i]} KDE",
                linewidth=1.8,
                alpha=0.95,
                zorder=3,
            )[0]
            self.ax.fill_between(
                x,
                y,
                color=line.get_color(),
                alpha=0.12,
                linewidth=0,
                zorder=2,
            )

        return None

    def labels(self, info_parameter: str) -> None:
        """
        Set histogram labels and legend.

        Parameters
        ----------
        info_parameter : str
            The info parameter to set the labels of the plot frame.

        Returns
        -------
        None
        """

        self.style_single_plot(
            title=f"{info_parameter} distribution",
            xlabel=self.parameter_axis_label(info_parameter),
            ylabel="Density",
        )
        self.ax.margins(x=0.04, y=0.12)
        self.ax.set_ylim(bottom=0)

        _, labels = self.ax.get_legend_handles_labels()
        if not labels:
            logger.warning("No data to plot.")
        else:
            self.show_legend(loc="best", ncol=min(3, len(labels)))

        return None

    def statistics(self, info_parameter: str) -> None:
        """
        Plot enabled mean and median guide lines.

        Parameters
        ----------
        info_parameter : str
            The info parameter to calculate the statistics of.

        Returns
        -------
        None
        """

        for guide in iter_histogram_guides(
            self.reader.energies,
            info_parameter,
            self.options,
        ):
            style = guide.feature.matplotlib_style.copy()
            style["linewidth"] = max(style["linewidth"], 1.35)
            style["zorder"] = 4
            self.ax.axvline(
                guide.value,
                label=guide.label,
                **style,
            )

        return None
