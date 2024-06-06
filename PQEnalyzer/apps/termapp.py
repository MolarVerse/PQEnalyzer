"""
This module allows the user to plot the data in the terminal.
"""
import signal
from InquirerPy import inquirer

from ..plots import TermPlot


class TermApp:
    """
    A class to plot the data in the terminal.

    Attributes
    ----------
    reader : Reader
        The Reader object to read the data.

    Methods
    -------
    """

    def __init__(self, reader):
        """
        Constructs all the necessary attributes for the TermApp object.

        Parameters
        ----------
        reader : Reader
            The Reader object to read the data.

        Returns
        -------
        None
        """

        self.reader = reader
        self.info = [
            *self.reader.energies[0].info,
        ][1:]

        return None

    def run(self):
        """
        Run the terminal application.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        result = inquirer.select(
            message="Select the information parameter to plot",
            choices=self.info,
            vi_mode=True,
            mandatory=True,
        ).execute()

        termplot = TermPlot(self.reader)
        termplot.plot(result)

        return None

    def start(self):
        """
        Start the terminal application.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        try:
            self.run()
            _exit = inquirer.confirm(
                message="Do you want to exit?",
                default=False,
                vi_mode=True,
                keybindings={
                    "interrupt": [{
                        "key": "c-d"
                    }]
                },
            ).execute()

            if _exit:
                return None

        except KeyboardInterrupt:
            return None

        return self.start()
