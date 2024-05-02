import customtkinter as ctk
import tkinter
import os
from PIL import Image

from ..config import BASE_PROJECT_PATH
from .plot_time import PlotTime


class App(ctk.CTk):
    """
    The main application class for the PQEnalyzer application. This class inherits from the CTK class.

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
        # self.icon = Image.open(os.path.join(BASE_PROJECT_PATH, "icons", "icon.ico"))
        # self.wm_iconbitmap()
        # self.iconphoto(False, self.icon)

        # set reader object and info parameters
        self.reader = reader
        self.info = [*self.reader.energies[0].info][
            1:
        ]  # get list of info parameters from first data object

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
        """
        # sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        # logo
        self.logo = ctk.CTkImage(
            Image.open(os.path.join(BASE_PROJECT_PATH, "icons", "icon.png")),
            size=(100, 100),
        )
        self.sidebar_image_label = ctk.CTkLabel(
            self.sidebar_frame, image=self.logo, text=""
        )
        self.sidebar_image_label.grid(row=0, column=0, pady=10, padx=10)
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="PQEnalyzer",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.grid(row=1, column=0, padx=10, pady=10)

        # change appearance mode
        self.appearance_mode_label = ctk.CTkLabel(
            self.sidebar_frame, text="Appearance Mode:", anchor="w"
        )
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["System", "Light", "Dark"],
            command=self.__change_appearance_mode_event,
        )
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.appearance_mode_optionemenu.set(
            "System"
        )  # set the default appearance mode to System

    def __build_button_menu(self):
        """
        Build the main window.
        """
        self.plot_frame = ctk.CTkFrame(self, width=200)
        self.plot_frame.grid(
            row=2, column=1, sticky="nsew", padx=(20, 20), pady=(10, 10)
        )
        self.plot_frame.grid_rowconfigure(3, weight=1)
        self.plot_frame.grid_columnconfigure(2, weight=1)

        def validate_number(value):
            """
            Validate if the input is a number.
            """
            return value.isdigit() or value == ""

        def toggle_entry_state():
            """
            Toggle the state of the entry.
            """
            if self.follow.get():
                self.interval.configure(state="normal")
                self.interval.insert(0, "1000")
            else:
                self.interval.delete(0, ctk.END)
                self.interval.configure(state="disabled")

        self.follow = tkinter.BooleanVar()
        self.main_button_2 = ctk.CTkCheckBox(
            master=self.plot_frame,
            border_width=2,
            text="Follow",
            variable=self.follow,
            command=toggle_entry_state,
        )
        self.main_button_2.grid(
            row=1, column=1, padx=(10, 10), pady=(10, 10), sticky="nsew"
        )

        self.plot_main_data = tkinter.BooleanVar()
        self.main_button_3 = ctk.CTkCheckBox(
            master=self.plot_frame,
            border_width=2,
            text="No Data",
            variable=self.plot_main_data,
        )
        self.main_button_3.grid(
            row=1, column=0, padx=(10, 10), pady=(10, 10), sticky="nsew"
        )

        self.interval = ctk.CTkEntry(
            self.plot_frame,
            width=10,
            validate="key",
            validatecommand=(self.register(validate_number), "%P"),
        )
        self.interval.grid(row=2, column=1, padx=10, pady=5, sticky="we")
        self.interval.configure(state="disabled")  # Initially disabled

        self.interval_label = ctk.CTkLabel(
            self.plot_frame, text="Interval (ms):", anchor="w"
        )
        self.interval_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        # create main frame with widgets
        self.main_button_1 = ctk.CTkButton(
            master=self.plot_frame,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "#DCE4EE"),
            text="Plot",
            command=self.__plot_button_event,
        )
        self.main_button_1.grid(
            row=3, column=0, columnspan=2, padx=(20, 20), pady=(20, 20), sticky="nsew"
        )

    def __build_info_option_menu(self):
        """
        Build the info selection window.
        """
        self.info_frame = ctk.CTkFrame(self, width=200)
        self.info_frame.grid(
            row=0, column=1, sticky="nsew", padx=(20, 20), pady=(10, 10)
        )
        self.info_frame.grid_rowconfigure(2, weight=1)
        self.info_frame.grid_columnconfigure(1, weight=1)

        self.info_label = ctk.CTkLabel(
            self.info_frame, text="Parameter:", font=ctk.CTkFont(size=15, weight="bold")
        )
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
            self.info[0]
        )  # set the default info parameter to the first one

    def __build_settings_menu(self):
        """
        Build the settings window.
        """
        self.settings_frame = ctk.CTkFrame(self, width=200)
        self.settings_frame.grid(
            row=1, column=1, sticky="nsew", padx=(20, 20), pady=(10, 10)
        )
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
        self.cummulative_average = ctk.CTkCheckBox(
            self.settings_frame, text="Cummulative Average"
        )
        self.cummulative_average.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.auto_correlation = ctk.CTkCheckBox(
            self.settings_frame, text="Auto Correlation"
        )
        self.auto_correlation.grid(row=4, column=0, padx=10, pady=5, sticky="w")

        def validate_number(value):
            """
            Validate if the input is a number.
            """
            return value.isdigit() or value == ""

        def toggle_entry_state():
            """
            Toggle the state of the entry.
            """
            if self.running_average.get():
                self.window_size.configure(state="normal")
                self.window_size.insert(0, "1000")
            else:
                self.window_size.delete(0, ctk.END)
                self.window_size.configure(state="disabled")

        self.running_average = ctk.CTkCheckBox(
            self.settings_frame, text="Running Average", command=toggle_entry_state
        )
        self.running_average.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.running_average_window_size_label = ctk.CTkLabel(
            self.settings_frame, text="Window Size:", anchor="w"
        )
        self.running_average_window_size_label.grid(
            row=6, column=0, padx=10, pady=5, sticky="w"
        )
        self.window_size = ctk.CTkEntry(
            self.settings_frame,
            width=10,
            validate="key",
            validatecommand=(self.register(validate_number), "%P"),
        )
        self.window_size.grid(row=7, column=0, padx=10, pady=5, sticky="we")
        self.window_size.configure(state="disabled")  # Initially disabled

    def __change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def __change_info_event(self, new_info: str):
        self.__selected_info = new_info

    def __plot_button_event(self):
        """
        Plot the data and checks if the user wants to follow the plot.
        """
        plot = PlotTime(self.reader)

        if self.follow.get():
            plot.live_plot(self.__selected_info, int(self.interval.get()))
        else:
            plot.plot(self.__selected_info)
