"""
A module containing the App class.

...

Classes
-------
App
    A class for the main window of the PQEnalyzer application.
"""

import customtkinter
import tkinter as tk
import os

from .custom_theme import default_theme
from .read_files import read_energy_files

class App(customtkinter.CTk):
    """
    The main application class for the PQEnalyzer application. This class inherits from the CTK class.

    ...

    Attributes
    ----------
    None
    """

    def __init__(self, filenames):

        self.read(filenames)

        super().__init__()

        default_theme()

        self.title("PQEnalyzer - MolarVerse")

        # load icon photo
        self.iconphoto(True, tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "icons", "icon.png")))

        


    def read(self, filenames):
        """
        Reads the data from the specified files.

        Parameters
        ----------
        filenames : list of str
            The names of the files to read the data from.
        """

        self.data = read_energy_files(filenames)
