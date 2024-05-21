"""
A module for reading energy files. The Reader class reads energy files using the
EnergyFileReader class from the PQAnalysis.io module.
"""

from PQAnalysis.io import EnergyFileReader


class Reader:
    """
    A class for reading energy files. Using the EnergyFileReader class from
    the PQAnalysis.io module.

    ...

    Attributes
    ----------
    energies : list
        A list of EnergyFileReader objects.
    filenames : list
        A list of filenames.
    md_format : MDEngineFormat
        The molecular dynamics engine format.

    Methods
    -------
    read()
        Read energy files and return a list of EnergyFileReader objects.


    Examples
    --------
    >>> reader = Reader(["md-01.en", "md-02.en"], MDEngineFormat.PQ)
    >>> reader.read()
    >>> reader.energies[0].info
    ['SIMULATION-TIME', 'ENERGY', 'KINETIC', 'POTENTIAL', 'TEMPERATURE', 'PRESSURE']
    >>> reader.energies[0].data['ENERGY']
    [0.0, -0.5, -1.0, -1.5, -2.0]
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
        self.filenames = filenames
        self.md_format = md_format
        self.read()

    def read(self):
        """
        Read energy files and return a list of EnergyFileReader objects.

        Returns
        -------
        None
        """

        if len(self.filenames) == 0:
            raise ValueError(
                "The list of filenames is empty. Provide a list of filenames.")

        energy_files = []
        for filename in self.filenames:
            energy_files.append(
                EnergyFileReader(filename, engine_format=self.md_format))

        read_energy_files = []
        for energy_file in energy_files:
            read_energy_file = energy_file.read()
            read_energy_files.append(read_energy_file)

        if not self.__check_info_length(read_energy_files):
            raise ValueError(
                "The energy files do not have the same length of info.")

        self.energies = read_energy_files

    def read_last(self):
        """
        Read the last energy file and adds it to the list of EnergyFileReader objects.

        Returns
        -------
        None
        """
        energy_file = EnergyFileReader(self.filenames[-1],
                                       engine_format=self.md_format)
        self.energies[-1] = energy_file.read()

    def __check_info_length(self, read_energy_files):
        """
        Check if all the energy files have the same length of info.

        Returns
        -------
        bool
        """

        info_lengths = []
        for energy_file in read_energy_files:
            info_lengths.append(len(energy_file.info))

        if len(set(info_lengths)) == 1:
            return True
        else:
            return False
