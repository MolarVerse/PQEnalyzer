"""
Interactive terminal application for parameter selection and plotting.
"""
import signal
from InquirerPy import inquirer

from ..plots import TermPlot


class TermApp:
    """
    Prompt for an energy parameter and render it with TermPlot.

    Attributes
    ----------
    reader : Reader
        The Reader object to read the data.

    """

    def __init__(self, reader):
        """
        Store the Reader and derive selectable parameter names.

        Parameters
        ----------
        reader : Reader
            The Reader object to read the data.

        """

        self.reader = reader
        self.info = [
            *self.reader.energies[0].info,
        ][1:]

        return None

    def run(self):
        """
        Ask for one parameter and draw a terminal plot once.
        """

        result = inquirer.select(
            message="Select the information parameter to plot",
            choices=self.info,
            vi_mode=True,
            mandatory=True,
        ).execute()

        difference = False
        if len(self.reader.energies) == 2:
            difference = inquirer.confirm(
                message="Plot difference between the two input files?",
                default=False,
                vi_mode=True,
            ).execute()

        termplot = TermPlot(self.reader)
        termplot.plot(result, difference=difference)

        return None

    def start(self):
        """
        Run the terminal prompt loop until the user exits or interrupts.
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
