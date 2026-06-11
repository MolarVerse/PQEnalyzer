"""
Interactive terminal application for parameter selection and plotting.
"""
import signal
from InquirerPy import inquirer

from ..energy_access import parameter_unit, simulation_time
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

    def plot(self, info_parameter, difference=False):
        """
        Render one parameter without prompting.
        """

        resolved_parameter = self.resolve_parameter(info_parameter)

        if difference and len(self.reader.energies) != 2:
            raise ValueError("Difference plotting requires exactly two files.")

        termplot = TermPlot(self.reader)
        termplot.plot(resolved_parameter, difference=difference)

        return None

    def summary(self):
        """
        Return a text summary for the loaded files and available parameters.
        """

        lines = [
            "PQEnalyzer input summary",
            f"Files: {len(self.reader.filenames)}",
        ]

        for filename, energy in zip(self.reader.filenames,
                                    self.reader.energies):
            lines.append(
                f"  {filename}: {len(simulation_time(energy))} rows")

        lines.extend([
            f"Parameters: {len(self.info)}",
        ])

        for parameter in self.info:
            unit = parameter_unit(self.reader.energies[0], parameter)
            lines.append(f"  {parameter} [{unit}]")

        return "\n".join(lines)

    def resolve_parameter(self, info_parameter):
        """
        Return the canonical parameter name for user-provided input.
        """

        if info_parameter in self.info:
            return info_parameter

        normalized_parameter = info_parameter.casefold()
        for parameter in self.info:
            if parameter.casefold() == normalized_parameter:
                return parameter

        raise ValueError(
            f"Unknown parameter: {info_parameter}. "
            f"Available parameters: {', '.join(self.info)}.")

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

        self.plot(result, difference=difference)

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
