from PQAnalysis.io.energyFileReader import EnergyFileReader

class Reader:
    """
    A class for reading energy files.

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
    """

    def __init__(self, filenames, md_format):
        """
        Constructs all the necessary attributes for the Reader object.
        """
        self.energies = []
        self.filenames = filenames
        self.md_format = md_format
        self.read()

    def read(self):
        """
        Read energy files and return a list of EnergyFileReader objects.
        """

        if len(self.filenames) == 0:
            raise ValueError("The list of filenames is empty.")

        energy_files = []
        for filename in self.filenames:
            energy_files.append(EnergyFileReader(filename, format=self.md_format))

        read_energy_files = []
        for energy_file in energy_files:
            read_energy_file = energy_file.read()
            read_energy_files.append(read_energy_file)
        
        if not self.__check_info_length(read_energy_files):
            raise ValueError("The energy files do not have the same length of info.")      

        self.energies = read_energy_files

    def __check_info_length(self, read_energy_files):
        """
        Check if all the energy files have the same length of info.
        """
        info_lengths = []
        for energy_file in read_energy_files:
            info_lengths.append(len(energy_file.info))

        if len(set(info_lengths)) == 1:
            return True
        else:
            return False