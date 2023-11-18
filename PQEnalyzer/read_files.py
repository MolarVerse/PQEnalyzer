"""
This module contains functions to read energy files.

Functions
---------
read_energy_files(filenames)
    Read energy files and return a list of EnergyFileReader objects.
check_info_length(energy_files)
    Check if all the energy files have the same length of info.
"""

from PQAnalysis.io.energyFileReader import EnergyFileReader

def read_energy_files(filenames):
    """
    Read energy files and return a list of EnergyFileReader objects.
    """

    if len(filenames) == 0:
        raise ValueError("The list of filenames is empty.")

    energy_files = []
    for filename in filenames:
        energy_files.append(EnergyFileReader(filename))

    read_energy_files = []
    for energy_file in energy_files:
        read_energy_file = energy_file.read()
        read_energy_files.append(read_energy_file)
    
    if not check_info_length(read_energy_files):
        raise ValueError("The energy files do not have the same length of info.")      

    return read_energy_files

def check_info_length(read_energy_files):
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