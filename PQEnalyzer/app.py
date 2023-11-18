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

class App(customtkinter.CTk):
    """
    The main application class for the PQEnalyzer application. This class inherits from the CTK class.

    ...

    Attributes
    ----------
    None
    """

    def __init__(self):
        super().__init__()

        default_theme()

        self.title("PQEnalyzer - MolarVerse")

        # load icon photo
        self.iconphoto(True, tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "icons", "icon.png")))

