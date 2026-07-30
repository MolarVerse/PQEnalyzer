"""
Reader orchestration for PQAnalysis energy files.

PQEnalyzer deliberately delegates file parsing to PQAnalysis. The Reader class
adds the application-specific guarantees needed before a GUI or terminal plot
can compare multiple files.
"""

from PQAnalysis.io import EnergyFileReader
from PQAnalysis.traj import MDEngineFormat


class Reader:
    """
    Read energy files with PQAnalysis and validate plot compatibility.

    PQAnalysis owns the energy-file parsing. This wrapper keeps the
    PQEnalyzer-specific behavior around multi-file reads: every selected file
    must use compatible units for parameters that appear in more than one file.

    Attributes
    ----------
    energies : list
        A list of parsed PQAnalysis Energy objects.
    filenames : list
        The energy filenames to read.
    md_format : MDEngineFormat
        The molecular dynamics engine format.

    Methods
    -------
    read()
        Read all configured energy files.
    read_last()
        Refresh only the last configured energy file.


    Examples
    --------
    >>> reader = Reader(["md-01.en", "md-02.en"], MDEngineFormat.PQ)
    >>> reader.read()
    >>> reader.energies[0].temperature_unit
    'K'
    """

    def __init__(self, filenames, md_format):
        """
        Read the configured files immediately.

        Parameters
        ----------
        filenames : list
            A list of filenames.
        md_format : MDEngineFormat
            The molecular dynamics engine format.

        Raises
        ------
        ValueError
            If no filenames are provided or if multiple files are not
            compatible for plotting.
        """

        self.energies = []
        self.filenames = list(filenames)
        self.md_format = md_format
        self.read()

    def read(self):
        """
        Read all energy files through PQAnalysis and validate compatibility.

        Existing ``energies`` are replaced only after all files have been read
        and validated.
        """

        self.__validate_filenames()

        energies = [
            self.__read_energy_file(filename) for filename in self.filenames
        ]

        self.__validate_energy_compatibility(energies)

        self.energies = energies

    def read_last(self):
        """
        Refresh the last energy file while preserving compatibility checks.

        This is used by live/follow plotting so the newest file can grow on
        disk without rebuilding the whole Reader object.
        """

        self.__validate_filenames()

        refreshed_energy = self.__read_energy_file(self.filenames[-1])
        refreshed_energies = [*self.energies]
        refreshed_energies[-1] = refreshed_energy

        self.__validate_energy_compatibility(refreshed_energies)
        self.energies[-1] = refreshed_energy

    def __read_energy_file(self, filename):
        """
        Read one energy file with PQAnalysis using this Reader's MD format.
        """

        return EnergyFileReader(filename,
                                engine_format=self.md_format).read()

    def __validate_filenames(self):
        """
        Reject empty input before handing control to PQAnalysis.
        """

        if len(self.filenames) == 0:
            raise ValueError(
                "The list of filenames is empty. Provide a list of filenames.")

    def __validate_energy_compatibility(self, energies):
        """
        Check if shared energy parameters use matching units.

        Multi-file plots can omit files that do not expose a selected
        parameter. If two files expose the same parameter label, that label
        must still use the same unit in both files.
        """

        units_by_parameter = {}
        reference_filename_by_parameter = {}

        for filename, energy in zip(self.filenames, energies):
            for parameter, unit in energy.units.items():
                if parameter not in units_by_parameter:
                    units_by_parameter[parameter] = unit
                    reference_filename_by_parameter[parameter] = filename
                    continue

                if unit != units_by_parameter[parameter]:
                    reference_filename = reference_filename_by_parameter[
                        parameter]
                    raise ValueError(
                        "The energy files do not have the same units for "
                        f"{parameter}: {reference_filename} and {filename}.")
