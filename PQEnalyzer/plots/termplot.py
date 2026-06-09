"""
Terminal plotting implementation.
"""
import plotext as plt

from .._logging import get_logger
from ..energy_access import difference_series, parameter_unit, series
from .labels import unique_path_labels


logger = get_logger(__name__)


class TermPlot:
    """
    Render selected energy parameters with plotext.

    Attributes
    ----------
    reader : Reader
        Reader containing parsed energy files.

    Use ``plot`` to draw a selected parameter for all Reader inputs.
    """

    def __init__(self, reader):
        """
        Store the Reader used for terminal plotting.

        Parameters
        ----------
        reader : Reader
            The Reader object to read the data.

        """

        self.reader = reader

    def plot(self, info_parameter, difference=False):
        """
        Plot one selected parameter for every input file.

        Parameters
        ----------
        info_parameter : str
            The information parameter to plot.
        difference : bool
            If true, plot the first input file minus the second input file.

        """
        if difference:
            try:
                delta_series = difference_series(
                    self.reader.energies, info_parameter)
            except ValueError as error:
                logger.warning("%s", error)
                return None

            plt.plot(
                delta_series.time,
                delta_series.values,
                label="Difference (1 - 2)",
            )
        else:
            labels = unique_path_labels(self.reader.filenames)
            for i, energy in enumerate(self.reader.energies):
                energy_series = series(energy, info_parameter)
                plt.plot(
                    energy_series.time,
                    energy_series.values,
                    label=labels[i],
                )

        plt.xlabel("Simulation Time")
        plt.ylabel(
            f"{info_parameter} / "
            f"{parameter_unit(self.reader.energies[0], info_parameter)}"
        )
        plt.show()
        plt.clear_figure()
        return None
