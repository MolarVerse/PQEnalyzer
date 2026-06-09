"""
Histogram/KDE plotting for PQ energy parameters.
"""

import os
from scipy.stats import gaussian_kde
import numpy as np

from ..statistics import Statistic
from ..energy_access import concatenate_series, parameter_unit, parameter_values
from .._logging import get_logger
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

        for i, energy in enumerate(self.reader.energies):
            basename = os.path.basename(self.reader.filenames[i])
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
            self.ax.plot(x, y, label=f"{basename} KDE")

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

        self.ax.set_ylabel("Density")

        self.ax.ticklabel_format(axis="both", style="sci")

        self.ax.set_xlabel(
            f"{info_parameter} / "
            f"{parameter_unit(self.reader.energies[0], info_parameter)}"
        )

        # Check if label is empty
        if self.ax.get_legend_handles_labels()[1] == []:
            logger.warning("No data to plot.")
        else:
            # legend outside of plot
            self.ax.legend(
                loc="upper center",
                bbox_to_anchor=(0.5, 1.15),
                ncol=5,
                fancybox=True,
                shadow=True,
            )

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

        energy_series = concatenate_series(self.reader.energies,
                                           info_parameter)

        if self.mean:
            # calculate mean and plot
            _, y = Statistic.mean_values(energy_series.time,
                                         energy_series.values)
            self.ax.vlines(float(y[0]),
                           0,
                           self.ax.get_ylim()[1],
                           label="Mean",
                           linestyles="--",
                           colors="blue")

        if self.median:
            # calculate median and plot
            _, y = Statistic.median_values(energy_series.time,
                                           energy_series.values)
            # plot dependent y_max of histogram
            self.ax.vlines(float(y[0]),
                           0,
                           self.ax.get_ylim()[1],
                           label="Median",
                           linestyles="--",
                           colors="red")

        return None
