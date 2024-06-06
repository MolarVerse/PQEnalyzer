"""
The plot module to plot the data in the terminal.
"""

import os
import plotext as plt


class TermPlot:
    """
    A class to plot the data in the terminal.

    Attributes
    ----------
    Reader : Reader
        The Reader object to read the data.

    Methods
    -------
    plot(info_parameter)
        Plot the data in the terminal.
    """

    def __init__(self, reader):
        """
        Constructs all the necessary attributes for the TermPlot object.

        Parameters
        ----------
        reader : Reader
            The Reader object to read the data.

        Returns
        -------
        None
        """

        self.reader = reader

    def plot(self, info_parameter):
        """
        Plot the data.

        Parameters
        ----------
        info_parameter : str
            The information parameter to plot.

        Returns
        -------
        None
        """
        for i, energy in enumerate(self.reader.energies):
            basename = os.path.basename(self.reader.filenames[i])
            plt.plot(
                energy.simulation_time,
                energy.data[energy.info[info_parameter]],
                label=basename,
            )
            plt.xlabel("Simulation Time")
            plt.ylabel(
                f"{info_parameter} / {self.reader.energies[0].units[info_parameter]}"
            )
        plt.show()
        plt.clear_figure()
