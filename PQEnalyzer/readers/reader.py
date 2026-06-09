"""
Reader orchestration for PQAnalysis energy files.
"""

from PQAnalysis.io import EnergyFileReader


class Reader:
    """
    Read energy files with PQAnalysis and validate plot compatibility.

    PQAnalysis owns the energy-file parsing. This wrapper keeps the
    PQEnalyzer-specific behavior around multi-file reads: every selected file
    must expose the same parameter mapping and units before plotting.

    ...

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
    >>> reader.energies[0].temperature
    array([...])
    """

    def __init__(self, filenames, md_format):
        """
        Constructs all the necessary attributes for the Reader object.

        Parameters
        ----------
        filenames : list
            A list of filenames.
        md_format : MDEngineFormat
            The molecular dynamics engine format.

        Returns
        -------
        None
        """

        self.energies = []
        self.filenames = list(filenames)
        self.md_format = md_format
        self.read()

    def read(self):
        """
        Read all energy files through PQAnalysis and validate compatibility.

        Returns
        -------
        None
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

        Returns
        -------
        None
        """

        self.__validate_filenames()

        refreshed_energy = self.__read_energy_file(self.filenames[-1])
        refreshed_energies = [*self.energies]
        refreshed_energies[-1] = refreshed_energy

        self.__validate_energy_compatibility(refreshed_energies)
        self.energies[-1] = refreshed_energy

    def __read_energy_file(self, filename):
        """
        Read one energy file with PQAnalysis.
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
        Check if all energy files expose the same parameters and units.

        Returns
        -------
        None
        """

        reference_info = energies[0].info
        reference_units = energies[0].units

        for index, energy in enumerate(energies[1:], start=1):
            if energy.info != reference_info:
                raise ValueError(
                    "The energy files do not have the same info parameters: "
                    f"{self.filenames[0]} and {self.filenames[index]}.")

            if energy.units != reference_units:
                raise ValueError(
                    "The energy files do not have the same units: "
                    f"{self.filenames[0]} and {self.filenames[index]}.")
