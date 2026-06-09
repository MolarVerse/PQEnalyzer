"""
Terminal plotting implementation.
"""

import os
import plotext as plt

from ..energy_access import parameter_unit, series


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

    def plot(self, info_parameter):
        """
        Plot one selected parameter for every input file.

        Parameters
        ----------
        info_parameter : str
            The information parameter to plot.

        """
        for i, energy in enumerate(self.reader.energies):
            basename = os.path.basename(self.reader.filenames[i])
            energy_series = series(energy, info_parameter)
            plt.plot(
                energy_series.time,
                energy_series.values,
                label=basename,
            )
            plt.xlabel("Simulation Time")
            plt.ylabel(
                f"{info_parameter} / "
                f"{parameter_unit(self.reader.energies[0], info_parameter)}"
            )
        plt.show()
        plt.clear_figure()
