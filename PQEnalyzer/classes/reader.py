from PQAnalysis.io.energyFileReader import EnergyFileReader
from PQAnalysis.traj.formats import MDEngineFormat

class Reader:

    def __init__(self, filenames, md_format):
        """
        Constructs all the necessary attributes for the Reader object.
        """    
        self.__filenames = filenames
        self.__md_format = md_format
        self.read()

    def read(self):
        """
        Read energy files and return a list of EnergyFileReader objects.
        """

        if len(self.__filenames) == 0:
            raise ValueError("The list of filenames is empty.")

        energy_files = []
        for filename in self.__filenames:
            energy_files.append(EnergyFileReader(filename, format=self.__md_format))

        read_energy_files = []
        for energy_file in energy_files:
            read_energy_file = energy_file.read()
            read_energy_files.append(read_energy_file)
        
        if not self.__check_info_length(read_energy_files):
            raise ValueError("The energy files do not have the same length of info.")      

        self.data = read_energy_files

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
        
    def get_data(self):
        """
        Return the data.
        """
        return self.data
    
    def get_filenames(self):
        """
        Return the filenames.
        """
        return self.__filenames
    
    def get_md_format(self):
        """
        Return the md_format.
        """
        return self.md_format

    def set_filenames(self, filenames):
        """
        Set the filenames.
        """
        self.__filenames = filenames

    def set_md_format(self, md_format):
        """
        Set the md_format.
        """
        self.md_format = md_format