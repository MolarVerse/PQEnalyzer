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

from ..config import BASE_PROJECT_PATH

class App(customtkinter.CTk):
    """
    The main application class for the PQEnalyzer application. This class inherits from the CTK class.

    ...

    Attributes
    ----------
    None
    """

    def __init__(self, reader=None):
        """
        Constructs all the necessary attributes for the App object.
        """
        super().__init__()
        self.__default_theme()
        self.title("PQEnalyzer - MolarVerse")
        # load icon photo
        self.iconphoto(True, tk.PhotoImage(file=os.path.join(BASE_PROJECT_PATH, "..", "icons", "icon.png")))
        self.reader = reader
    
    def __default_theme(self):
        """
        Sets the default theme for the application.
        """
        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")

