"""
This module allows the user to plot the data in the terminal.
"""
import signal
import inquirer

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

        signal.signal(signal.SIGINT, self.signal_handler)

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

        questions = [
            inquirer.List(
                "info_parameter",
                message="Select the information parameter to plot",
                choices=self.info,
            )
        ]

        answers = inquirer.prompt(questions)
        termplot = TermPlot(self.reader)
        termplot.plot(answers["info_parameter"])

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

        self.run()
        _exit = [
            inquirer.questions.Confirm(
                "exit", message="Do you want to exit?", default=False
            )
        ]
        answer = inquirer.prompt(_exit)
        if answer["exit"]:
            return None

        return self.start()

    def signal_handler(self, signal, frame):
        """
        Handle the signal.

        Parameters
        ----------
        signal : int
            The signal number.
        frame : Frame
            The frame.

        Returns
        -------
        None
        """
        exit(0)
