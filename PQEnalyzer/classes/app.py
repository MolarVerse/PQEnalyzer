"""
A module containing the App class.

...

Classes
-------
App
    A class for the main window of the PQEnalyzer application.
"""

import customtkinter as ctk
import tkinter
import os
from PIL import Image

from ..config import BASE_PROJECT_PATH
from .plot import Plot

class App(ctk.CTk):
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
        self.iconphoto(True, tkinter.PhotoImage(file=os.path.join(BASE_PROJECT_PATH, "..", "icons", "icon.png")))
        
        # set reader
        self.reader = reader
        self.info = [*self.reader.energies[0].info][1:] # get list of info parameters from first data object

        # build window
        self.__build_sidebar()
        self.__build_main_window()
        self.__build_info_option_menu()
        self.__build_settings_window()

        # set plot object
        self.plot = Plot(self, self.reader)
    
    def __default_theme(self):
        """
        Sets the default theme for the application.
        """
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

    def __build_sidebar(self):
        """
        Build the main window.
        """
        # sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        # logo
        self.logo = ctk.CTkImage(Image.open(os.path.join(BASE_PROJECT_PATH, "..", "icons", "icon.png")), size=(100, 100))
        self.sidebar_image_label = ctk.CTkLabel(self.sidebar_frame, image=self.logo, text="")
        self.sidebar_image_label.grid(row=0, column=0, pady=10, padx=10)
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="PQEnalyzer", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=1, column=0, padx=10, pady=10)
       
        # change appearance mode
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["System", "Light", "Dark"],
                                                                       command=self.__change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.appearance_mode_optionemenu.set("System") # set the default appearance mode to System

    def __build_main_window(self):
        """
        Build the main window.
        """
        # create main frame with widgets
        self.main_button_1 = ctk.CTkButton(master=self, fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), text="Plot", command=self.__plot_button_event)
        self.main_button_1.grid(row=3, column=4, padx=(20, 20), pady=(20, 20), sticky="nsew")
        self.main_button_2 = ctk.CTkCheckBox(master=self, border_width=2, text="Follow")
        self.main_button_2.grid(row=3, column=3, padx=(20, 20), pady=(20, 20), sticky="nsew")

    def __build_info_option_menu(self):
        """
        Build the info selection window.
        """
        self.info_frame = ctk.CTkFrame(self, width=140)
        self.info_frame.grid(row=0, column=2, sticky="nsew", padx=(20, 20), pady=(20, 20))
        self.info_frame.grid_rowconfigure(2, weight=1)
        self.info_frame.grid_columnconfigure(0, weight=1)

        self.info_label = ctk.CTkLabel(self.info_frame, text="Infofile Parameters:",font=ctk.CTkFont(size=15, weight="bold"))
        self.info_label.grid(row=0, column=1, padx=20, pady=10)
        self.info_optionmenu = ctk.CTkOptionMenu(self.info_frame, values=self.info, command=self.__change_info_event, width=150, anchor="c")
        self.info_optionmenu.grid(row=1, column=1, padx=20, pady=10)
        self.__change_info_event(self.info[0]) # set the default info parameter to the first one

    def __build_settings_window(self):
        """
        Build the settings window.
        """
        self.settings_frame = ctk.CTkFrame(self, width=140)
        self.settings_frame.grid(row=1, column=2, sticky="nsew", padx=(20, 20), pady=(20, 20))
        self.settings_frame.grid_rowconfigure(2, weight=1)
        self.settings_frame.grid_columnconfigure(0, weight=1)

        self.settings_label = ctk.CTkLabel(self.settings_frame, text="Settings:",font=ctk.CTkFont(size=15, weight="bold"))
        self.settings_label.grid(row=0, column=0, padx=20, pady=10)


    def __change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
    
    def __change_info_event(self, new_info: str):
        self.__selected_info = new_info

    def __plot_button_event(self):
        print("Plotting... ", self.__selected_info)
        self.plot.plot(self.__selected_info)



