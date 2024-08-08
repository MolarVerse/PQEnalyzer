"""
This module contains the App class that is used to create the main application
window for the PQEnalyzer application.
"""

import os
import signal
import tkinter

import customtkinter as ctk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt

from .. import __base__
from ..plots import PlotTime, PlotHistogram


class App(ctk.CTk):
    """
    The main application class for the PQEnalyzer application. This class inherits
    from the CTK class.

    ...

    Attributes
    ----------
    reader : Reader
        The reader object that contains the data.

    Methods
    -------
    build()
        Build the main window.
    """

    def __init__(self, reader=None):
        """
        Constructs all the necessary attributes for the App object.
        """
        super().__init__()
        self.__default_theme()
        self.title("PQEnalyzer - MolarVerse")

        # load icon photo
        img = Image.open(os.path.join(__base__, "icons", "icon.png"))
        self.iconphoto(False, ImageTk.PhotoImage(img))

        # set the window size
        self.resizable(False, False)

        # set reader object and info parameters
        self.reader = reader
        self.info = [
            *self.reader.energies[0].info
        ][1:]  # get list of info parameters from first data object

        self.list_of_plots = []

        # sigint handler
        signal.signal(signal.SIGINT,
                      lambda sig, frame: self.destroy())  # close the app

    def destroy(self):
        """
        Destroy the app.
        """
        self.quit()
        del (self)

    def build(self):
        """
        Build the main window.
        """
        self.__build_sidebar()
        self.__build_button_menu()
        self.__build_info_option_menu()
        self.__build_settings_menu()

    def __default_theme(self):
        """
        Sets the default theme for the application.
        """
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

    def __build_sidebar(self):
        """
        Build the main window.

        Returns
        -------
        None
        """
        # sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        # logo
        self.logo = ctk.CTkImage(
            Image.open(os.path.join(__base__, "icons", "icon.png")),
            size=(100, 100),
        )
        self.sidebar_image_label = ctk.CTkLabel(self.sidebar_frame,
                                                image=self.logo,
                                                text="")
        self.sidebar_image_label.grid(row=0, column=0, pady=10, padx=10)
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="PQEnalyzer",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.grid(row=1, column=0, padx=10, pady=10)

        # change appearance mode
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame,
                                                  text="Appearance Mode:",
                                                  anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["System", "Light", "Dark"],
            command=self.__change_appearance_mode_event,
        )
        self.appearance_mode_optionemenu.grid(row=6,
                                              column=0,
                                              padx=20,
                                              pady=(10, 10))
        self.appearance_mode_optionemenu.set(
            "System")  # set the default appearance mode to System

    def __build_button_menu(self):
        """
        Build the main window.

        Returns
        -------
        None
        """
        self.plot_frame = ctk.CTkFrame(self, width=200)
        self.plot_frame.grid(row=2,
                             column=1,
                             sticky="nsew",
                             padx=(20, 20),
                             pady=(10, 10))
        self.plot_frame.grid_rowconfigure(4, weight=1)
        self.plot_frame.grid_columnconfigure(2, weight=1)

        self.follow = tkinter.BooleanVar()
        self.interval = None  # Initially None
        self.check_follow = ctk.CTkCheckBox(
            master=self.plot_frame,
            border_width=2,
            text="Follow",
            variable=self.follow,
            command=lambda: self.toggle_entry_state(
                self.check_follow, self.interval, default="1.0"))
        self.check_follow.grid(row=0,
                               column=1,
                               padx=(10, 10),
                               pady=(10, 10),
                               sticky="nsew")

        self.plot_main_data = tkinter.BooleanVar()
        self.check_nodata = ctk.CTkCheckBox(
            master=self.plot_frame,
            border_width=2,
            text="No Data",
            variable=self.plot_main_data,
        )
        self.check_nodata.grid(row=0,
                               column=0,
                               padx=(10, 10),
                               pady=(10, 10),
                               sticky="nsew")

        self.interval = ctk.CTkEntry(
            self.plot_frame,
            width=10,
            validate="key",
            validatecommand=(self.register(self.validate_number), "%P"),
        )
        self.interval.grid(row=1, column=1, padx=10, pady=5, sticky="we")
        self.interval.configure(state="disabled")  # Initially disabled

        self.interval_label = ctk.CTkLabel(self.plot_frame,
                                           text="Interval (s):",
                                           anchor="w")
        self.interval_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.button_plot = ctk.CTkButton(
            master=self.plot_frame,
            border_width=2,
            text="Plot",
            command=lambda: self.__plot_button_event(0),
        )

        self.button_plot.grid(row=2,
                              column=0,
                              columnspan=2,
                              padx=(10, 10),
                              pady=(10, 10),
                              sticky="nsew")

        self.button_hist = ctk.CTkButton(
            master=self.plot_frame,
            border_width=2,
            text="Histogram",
            command=lambda: self.__plot_button_event(1),
        )
        self.button_hist.grid(row=3,
                              column=0,
                              columnspan=2,
                              padx=(10, 10),
                              pady=(10, 10),
                              sticky="nsew")

        self.button_refresh = ctk.CTkButton(  # refresh button
            master=self.plot_frame,
            border_width=2,
            text="Refresh",
            command=self.__refresh_plots,
        )
        self.button_refresh.grid(row=4,
                                 column=0,
                                 columnspan=2,
                                 padx=(10, 10),
                                 pady=(10, 10),
                                 sticky="nsew")

    def __build_info_option_menu(self):
        """
        Build the info selection window.

        Returns
        -------
        None
        """
        self.info_frame = ctk.CTkFrame(self, width=200)
        self.info_frame.grid(row=0,
                             column=1,
                             sticky="nsew",
                             padx=(20, 20),
                             pady=(10, 10))
        self.info_frame.grid_rowconfigure(2, weight=1)
        self.info_frame.grid_columnconfigure(1, weight=1)

        self.info_label = ctk.CTkLabel(self.info_frame,
                                       text="Parameter:",
                                       font=ctk.CTkFont(size=15,
                                                        weight="bold"))
        self.info_label.grid(row=0, column=1, padx=20, pady=10, sticky="w")
        self.info_optionmenu = ctk.CTkOptionMenu(
            self.info_frame,
            values=self.info,
            command=self.__change_info_event,
            width=150,
            anchor="c",
        )
        self.info_optionmenu.grid(row=1, column=1, padx=20, pady=10)
        self.__change_info_event(
            self.info[0])  # set the default info parameter to the first one

    def __build_settings_menu(self):
        """
        Build the settings window.

        Returns
        -------
        None
        """
        self.settings_frame = ctk.CTkFrame(self, width=200)
        self.settings_frame.grid(row=1,
                                 column=1,
                                 sticky="nsew",
                                 padx=(20, 20),
                                 pady=(10, 10))
        self.settings_frame.grid_rowconfigure(8, weight=1)
        self.settings_frame.grid_columnconfigure(0, weight=1)

        self.settings_label = ctk.CTkLabel(
            self.settings_frame,
            text="Statistics:",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.settings_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.mean = ctk.CTkCheckBox(self.settings_frame, text="Mean")
        self.mean.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.median = ctk.CTkCheckBox(self.settings_frame, text="Median")
        self.median.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.cummulative_average = ctk.CTkCheckBox(self.settings_frame,
                                                   text="Cummulative Average")
        self.cummulative_average.grid(row=3,
                                      column=0,
                                      padx=10,
                                      pady=5,
                                      sticky="w")
        self.auto_correlation = ctk.CTkCheckBox(self.settings_frame,
                                                text="Auto Correlation")
        self.auto_correlation.grid(row=4,
                                   column=0,
                                   padx=10,
                                   pady=5,
                                   sticky="w")

        self.window_size = None  # Initially None
        self.running_average = ctk.CTkCheckBox(
            self.settings_frame,
            text="Running Average",
            command=lambda: self.toggle_entry_state(
                self.running_average, self.window_size, default="10"))
        self.running_average.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.running_average_window_size_label = ctk.CTkLabel(
            self.settings_frame, text="Window Size:", anchor="w")
        self.running_average_window_size_label.grid(row=6,
                                                    column=0,
                                                    padx=10,
                                                    pady=5,
                                                    sticky="w")
        self.window_size = ctk.CTkEntry(
            self.settings_frame,
            width=10,
            validate="key",
            validatecommand=(self.register(self.validate_number), "%P"),
        )
        self.window_size.grid(row=7, column=0, padx=10, pady=5, sticky="we")
        self.window_size.configure(state="disabled")  # Initially disabled

    def validate_number(self, value):
        """
        Validate if the input is a number.
        """
        return value == "" or value.replace(".", "", 1).isdigit()

    def toggle_entry_state(self, event, entry, default=""):
        """
        Toggle the state of the entry.
        """
        if event.get():
            entry.configure(state="normal")
            entry.insert(0, default)
        else:
            entry.delete(0, ctk.END)
            entry.configure(state="disabled")

    def __change_appearance_mode_event(self, new_appearance_mode: str):
        """ 
        Change the appearance mode of the app.
        """
        
        ctk.set_appearance_mode(new_appearance_mode)

    def __change_info_event(self, new_info: str):
        """
        Change the info parameter to plot.
        """

        self.__selected_info = new_info

    def __refresh_plots(self):
        """
        Refresh the plots. If the plot is closed, remove it from the list.

        Returns
        -------
        None
        """
        for plot in self.list_of_plots:

            if plot.figure.number not in plt.get_fignums():
                self.list_of_plots.remove(plot)
                continue

            plot.refresh()

    def __plot_button_event(self, event):
        """
        Plot the data and checks if the user wants to follow the plot.
        Appends the plot to the list of plots. If the user wants to follow the plot,
        the plot is updated at a given interval.

        Parameters
        ----------
        event : int
            The event that triggered the function. 0 for time plot, 1 for histogram plot.

        Returns
        -------
        None
        """

        if event == 0:
            plot = PlotTime(self)
        elif event == 1:
            plot = PlotHistogram(self)

        self.list_of_plots.append(plot)

        if self.follow.get():
            plot.follow(self.__selected_info, float(self.interval.get()))
        else:
            plot.simple(self.__selected_info)
