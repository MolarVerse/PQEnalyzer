"""
Layout builders for the PQEnalyzer GUI.
"""

import os
import tkinter

import customtkinter as ctk
from PIL import Image, ImageTk

from .. import __base__


def configure_default_theme():
    """
    Configure the default CustomTkinter theme.
    """

    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")


def configure_window(app):
    """
    Configure top-level window settings.
    """

    app.title("PQEnalyzer - MolarVerse")

    image = Image.open(os.path.join(__base__, "icons", "icon.png"))
    app.iconphoto(False, ImageTk.PhotoImage(image))

    app.resizable(False, False)


def build_sidebar(app, change_appearance_mode_callback):
    """
    Build the sidebar and theme selector.
    """

    app.sidebar_frame = ctk.CTkFrame(app, width=140, corner_radius=0)
    app.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
    app.sidebar_frame.grid_rowconfigure(4, weight=1)
    app.sidebar_frame.grid_columnconfigure(0, weight=1)

    app.logo = ctk.CTkImage(
        Image.open(os.path.join(__base__, "icons", "icon.png")),
        size=(100, 100),
    )
    app.sidebar_image_label = ctk.CTkLabel(app.sidebar_frame,
                                           image=app.logo,
                                           text="")
    app.sidebar_image_label.grid(row=0, column=0, pady=10, padx=10)
    app.logo_label = ctk.CTkLabel(
        app.sidebar_frame,
        text="PQEnalyzer",
        font=ctk.CTkFont(size=20, weight="bold"),
    )
    app.logo_label.grid(row=1, column=0, padx=10, pady=10)

    app.appearance_mode_label = ctk.CTkLabel(app.sidebar_frame,
                                             text="Appearance Mode:",
                                             anchor="w")
    app.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
    app.appearance_mode_optionemenu = ctk.CTkOptionMenu(
        app.sidebar_frame,
        values=["System", "Light", "Dark"],
        command=change_appearance_mode_callback,
    )
    app.appearance_mode_optionemenu.grid(row=6,
                                         column=0,
                                         padx=20,
                                         pady=(10, 10))
    app.appearance_mode_optionemenu.set("System")


def build_plot_controls(app, plot_button_callback, refresh_callback):
    """
    Build plot command controls.
    """

    app.plot_frame = ctk.CTkFrame(app, width=200)
    app.plot_frame.grid(row=2,
                        column=1,
                        sticky="nsew",
                        padx=(20, 20),
                        pady=(10, 10))
    app.plot_frame.grid_rowconfigure(4, weight=1)
    app.plot_frame.grid_columnconfigure(2, weight=1)

    app.follow = tkinter.BooleanVar()
    app.interval = None
    app.check_follow = ctk.CTkCheckBox(
        master=app.plot_frame,
        border_width=2,
        text="Follow",
        variable=app.follow,
        command=lambda: app.toggle_entry_state(
            app.check_follow, app.interval, default="1.0"))
    app.check_follow.grid(row=0,
                          column=1,
                          padx=(10, 10),
                          pady=(10, 10),
                          sticky="nsew")

    app.plot_main_data = tkinter.BooleanVar()
    app.check_nodata = ctk.CTkCheckBox(
        master=app.plot_frame,
        border_width=2,
        text="No Data",
        variable=app.plot_main_data,
    )
    app.check_nodata.grid(row=0,
                          column=0,
                          padx=(10, 10),
                          pady=(10, 10),
                          sticky="nsew")

    app.interval = ctk.CTkEntry(
        app.plot_frame,
        width=10,
        validate="key",
        validatecommand=(app.register(app.validate_number), "%P"),
    )
    app.interval.grid(row=1, column=1, padx=10, pady=5, sticky="we")
    app.interval.configure(state="disabled")

    app.interval_label = ctk.CTkLabel(app.plot_frame,
                                      text="Interval (s):",
                                      anchor="w")
    app.interval_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

    app.button_plot = ctk.CTkButton(
        master=app.plot_frame,
        border_width=2,
        text="Plot",
        command=lambda: plot_button_callback(0),
    )

    app.button_plot.grid(row=2,
                         column=0,
                         columnspan=2,
                         padx=(10, 10),
                         pady=(10, 10),
                         sticky="nsew")

    app.button_hist = ctk.CTkButton(
        master=app.plot_frame,
        border_width=2,
        text="Histogram",
        command=lambda: plot_button_callback(1),
    )
    app.button_hist.grid(row=3,
                         column=0,
                         columnspan=2,
                         padx=(10, 10),
                         pady=(10, 10),
                         sticky="nsew")

    app.button_refresh = ctk.CTkButton(
        master=app.plot_frame,
        border_width=2,
        text="Refresh",
        command=refresh_callback,
    )
    app.button_refresh.grid(row=4,
                            column=0,
                            columnspan=2,
                            padx=(10, 10),
                            pady=(10, 10),
                            sticky="nsew")


def build_parameter_selector(app, change_info_callback):
    """
    Build the parameter selection controls.
    """

    app.info_frame = ctk.CTkFrame(app, width=200)
    app.info_frame.grid(row=0,
                        column=1,
                        sticky="nsew",
                        padx=(20, 20),
                        pady=(10, 10))
    app.info_frame.grid_rowconfigure(2, weight=1)
    app.info_frame.grid_columnconfigure(1, weight=1)

    app.info_label = ctk.CTkLabel(app.info_frame,
                                  text="Parameter:",
                                  font=ctk.CTkFont(size=15, weight="bold"))
    app.info_label.grid(row=0, column=1, padx=20, pady=10, sticky="w")
    app.info_optionmenu = ctk.CTkOptionMenu(
        app.info_frame,
        values=app.info,
        command=change_info_callback,
        width=150,
        anchor="c",
    )
    app.info_optionmenu.grid(row=1, column=1, padx=20, pady=10)
    change_info_callback(app.info[0])


def build_settings_controls(app):
    """
    Build statistics option controls.
    """

    app.settings_frame = ctk.CTkFrame(app, width=200)
    app.settings_frame.grid(row=1,
                            column=1,
                            sticky="nsew",
                            padx=(20, 20),
                            pady=(10, 10))
    app.settings_frame.grid_rowconfigure(8, weight=1)
    app.settings_frame.grid_columnconfigure(0, weight=1)

    app.settings_label = ctk.CTkLabel(
        app.settings_frame,
        text="Statistics:",
        font=ctk.CTkFont(size=15, weight="bold"),
    )
    app.settings_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
    app.mean = ctk.CTkCheckBox(app.settings_frame, text="Mean")
    app.mean.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    app.median = ctk.CTkCheckBox(app.settings_frame, text="Median")
    app.median.grid(row=2, column=0, padx=10, pady=5, sticky="w")
    app.cummulative_average = ctk.CTkCheckBox(app.settings_frame,
                                              text="Cumulative Average")
    app.cummulative_average.grid(row=3,
                                 column=0,
                                 padx=10,
                                 pady=5,
                                 sticky="w")
    app.auto_correlation = ctk.CTkCheckBox(app.settings_frame,
                                           text="Auto Correlation")
    app.auto_correlation.grid(row=4,
                              column=0,
                              padx=10,
                              pady=5,
                              sticky="w")

    app.window_size = None
    app.running_average = ctk.CTkCheckBox(
        app.settings_frame,
        text="Running Average",
        command=lambda: app.toggle_entry_state(
            app.running_average, app.window_size, default="10"))
    app.running_average.grid(row=5, column=0, padx=10, pady=5, sticky="w")
    app.running_average_window_size_label = ctk.CTkLabel(
        app.settings_frame, text="Window Size:", anchor="w")
    app.running_average_window_size_label.grid(row=6,
                                               column=0,
                                               padx=10,
                                               pady=5,
                                               sticky="w")
    app.window_size = ctk.CTkEntry(
        app.settings_frame,
        width=10,
        validate="key",
        validatecommand=(app.register(app.validate_number), "%P"),
    )
    app.window_size.grid(row=7, column=0, padx=10, pady=5, sticky="we")
    app.window_size.configure(state="disabled")
