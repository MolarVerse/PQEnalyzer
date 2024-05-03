import os
from scipy.stats import gaussian_kde

from .plot import Plot
from .statistic import Statistic

class PlotHistogram(Plot):
    """
    The plot the parameters dependent histogram for the PQEnalyzer application.

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
        Constructs all the necessary attributes for the PlotHistogram object.

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
        Plot the main data on the plot frame.

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
            # plot kde of histogram
            kde = gaussian_kde(energy.data[energy.info[info_parameter]])
            x = range(
                int(min(energy.data[energy.info[info_parameter]])),
                int(max(energy.data[energy.info[info_parameter]])),
            )
            y = kde(x)
            self.ax.plot(x, y, label=f"{basename} KDE")
        
        return None

    def labels(self, info_parameter: str) -> None:
        """
        Set the labels of the plot frame using the info parameter.

        Parameters
        ----------
        info_parameter : str
            The info parameter to set the labels of the plot frame.

        Returns
        -------
        None
        """

        self.ax.set_ylabel("Density")

        self.ax.set_xlabel(
            f"{info_parameter} / {self.reader.energies[0].units[info_parameter]}"
        )

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
        Plot the statistics of the data dependent into the plot frame using the info parameter.
        Mean and/or median are calculated and plotted.

        Parameters
        ----------
        info_parameter : str
            The info parameter to calculate the statistics of.

        Returns
        -------
        None
        """

        if self.app.mean.get():
            # calculate mean and plot
            _, y = Statistic.mean(self.reader.energies, info_parameter)
            self.ax.vlines(
                y, 
                0, 
                self.ax.get_ylim()[1],
                label="Mean", 
                linestyles="--",
                colors="blue"
            )

        if self.app.median.get():
            # calculate median and plot
            _, y = Statistic.median(self.reader.energies, info_parameter)
            # plot dependent y_max of histogram
            self.ax.vlines(
                y,
                0,
                self.ax.get_ylim()[1],
                label="Median",
                linestyles="--",
                colors="red"
            )

        return None
