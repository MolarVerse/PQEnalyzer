"""
View classes for the PQEnalyzer GUI layout.

Each view owns a focused group of CustomTkinter widgets and mirrors the widget
attributes onto ``App`` for compatibility with existing plotting code. This
keeps ``App`` as the coordinator while making layout sections independently
testable.
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

    The icon is loaded here because it belongs to the root Tk window rather
    than one specific view class.
    """

    app.title("PQEnalyzer - MolarVerse")

    image = Image.open(os.path.join(__base__, "icons", "icon.png"))
    app.iconphoto(False, ImageTk.PhotoImage(image))

    app.resizable(False, False)


class SidebarView:
    """
    Sidebar logo and appearance-mode controls.

    Parameters
    ----------
    app : App
        Root application window.
    change_appearance_mode_callback : callable
        Callback invoked by the appearance-mode option menu.
    """

    def __init__(self, app, change_appearance_mode_callback):
        self.app = app
        self.change_appearance_mode_callback = change_appearance_mode_callback

        self.frame = ctk.CTkFrame(app, width=140, corner_radius=0)
        self.frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.frame.grid_rowconfigure(4, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.logo = ctk.CTkImage(
            Image.open(os.path.join(__base__, "icons", "icon.png")),
            size=(100, 100),
        )
        self.image_label = ctk.CTkLabel(self.frame,
                                        image=self.logo,
                                        text="")
        self.image_label.grid(row=0, column=0, pady=10, padx=10)
        self.logo_label = ctk.CTkLabel(
            self.frame,
            text="PQEnalyzer",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.grid(row=1, column=0, padx=10, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(
            self.frame,
            text="Appearance Mode:",
            anchor="w",
        )
        self.appearance_mode_label.grid(row=5,
                                        column=0,
                                        padx=20,
                                        pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self.frame,
            values=["System", "Light", "Dark"],
            command=change_appearance_mode_callback,
        )
        self.appearance_mode_optionemenu.grid(row=6,
                                              column=0,
                                              padx=20,
                                              pady=(10, 10))
        self.appearance_mode_optionemenu.set("System")

        app.sidebar_frame = self.frame
        app.logo = self.logo
        app.sidebar_image_label = self.image_label
        app.logo_label = self.logo_label
        app.appearance_mode_label = self.appearance_mode_label
        app.appearance_mode_optionemenu = self.appearance_mode_optionemenu


class PlotControlsView:
    """
    Plot command controls.

    This view exposes the ``follow``, ``plot_main_data`` and interval widgets on
    the app because ``Plot`` reads that state when a plot window is created or
    refreshed.
    """

    def __init__(self, app, plot_button_callback, refresh_callback):
        self.app = app
        self.plot_button_callback = plot_button_callback
        self.refresh_callback = refresh_callback

        self.frame = ctk.CTkFrame(app, width=200)
        self.frame.grid(row=2,
                        column=1,
                        sticky="nsew",
                        padx=(20, 20),
                        pady=(10, 10))
        self.frame.grid_rowconfigure(4, weight=1)
        self.frame.grid_columnconfigure(2, weight=1)

        self.follow = tkinter.BooleanVar()
        self.follow_checkbox = ctk.CTkCheckBox(
            master=self.frame,
            border_width=2,
            text="Follow",
            variable=self.follow,
            command=lambda: app.toggle_entry_state(
                self.follow_checkbox, self.interval_entry, default="1.0"))
        self.follow_checkbox.grid(row=0,
                                  column=1,
                                  padx=(10, 10),
                                  pady=(10, 10),
                                  sticky="nsew")

        self.plot_main_data = tkinter.BooleanVar()
        self.no_data_checkbox = ctk.CTkCheckBox(
            master=self.frame,
            border_width=2,
            text="No Data",
            variable=self.plot_main_data,
        )
        self.no_data_checkbox.grid(row=0,
                                   column=0,
                                   padx=(10, 10),
                                   pady=(10, 10),
                                   sticky="nsew")

        self.interval_entry = ctk.CTkEntry(
            self.frame,
            width=10,
            validate="key",
            validatecommand=(app.register(app.validate_number), "%P"),
        )
        self.interval_entry.grid(row=1,
                                 column=1,
                                 padx=10,
                                 pady=5,
                                 sticky="we")
        self.interval_entry.configure(state="disabled")

        self.interval_label = ctk.CTkLabel(self.frame,
                                           text="Interval (s):",
                                           anchor="w")
        self.interval_label.grid(row=1,
                                 column=0,
                                 padx=10,
                                 pady=5,
                                 sticky="w")

        self.plot_button = ctk.CTkButton(
            master=self.frame,
            border_width=2,
            text="Plot",
            command=lambda: plot_button_callback(0),
        )
        self.plot_button.grid(row=2,
                              column=0,
                              columnspan=2,
                              padx=(10, 10),
                              pady=(10, 10),
                              sticky="nsew")

        self.histogram_button = ctk.CTkButton(
            master=self.frame,
            border_width=2,
            text="Histogram",
            command=lambda: plot_button_callback(1),
        )
        self.histogram_button.grid(row=3,
                                   column=0,
                                   columnspan=2,
                                   padx=(10, 10),
                                   pady=(10, 10),
                                   sticky="nsew")

        self.refresh_button = ctk.CTkButton(
            master=self.frame,
            border_width=2,
            text="Refresh",
            command=refresh_callback,
        )
        self.refresh_button.grid(row=4,
                                 column=0,
                                 columnspan=2,
                                 padx=(10, 10),
                                 pady=(10, 10),
                                 sticky="nsew")

        app.plot_frame = self.frame
        app.follow = self.follow
        app.check_follow = self.follow_checkbox
        app.plot_main_data = self.plot_main_data
        app.check_nodata = self.no_data_checkbox
        app.interval = self.interval_entry
        app.interval_label = self.interval_label
        app.button_plot = self.plot_button
        app.button_hist = self.histogram_button
        app.button_refresh = self.refresh_button


class ParameterSelectorView:
    """
    Energy-parameter selection controls.

    The selector initializes the app's selected parameter immediately so plot
    buttons can be used without first changing the option menu.
    """

    def __init__(self, app, change_info_callback):
        self.app = app
        self.change_info_callback = change_info_callback

        self.frame = ctk.CTkFrame(app, width=200)
        self.frame.grid(row=0,
                        column=1,
                        sticky="nsew",
                        padx=(20, 20),
                        pady=(10, 10))
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        self.label = ctk.CTkLabel(
            self.frame,
            text="Parameter:",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.label.grid(row=0, column=1, padx=20, pady=10, sticky="w")
        self.optionmenu = ctk.CTkOptionMenu(
            self.frame,
            values=app.info,
            command=change_info_callback,
            width=150,
            anchor="c",
        )
        self.optionmenu.grid(row=1, column=1, padx=20, pady=10)
        change_info_callback(app.info[0])

        app.info_frame = self.frame
        app.info_label = self.label
        app.info_optionmenu = self.optionmenu


class StatisticsControlsView:
    """
    Statistics option controls.

    Plot classes read these checkboxes directly from ``App`` when they collect
    plotting options, so this view assigns the same attributes that older App
    code created inline.
    """

    def __init__(self, app):
        self.app = app

        self.frame = ctk.CTkFrame(app, width=200)
        self.frame.grid(row=1,
                        column=1,
                        sticky="nsew",
                        padx=(20, 20),
                        pady=(10, 10))
        self.frame.grid_rowconfigure(8, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(
            self.frame,
            text="Statistics:",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.mean = ctk.CTkCheckBox(self.frame, text="Mean")
        self.mean.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.median = ctk.CTkCheckBox(self.frame, text="Median")
        self.median.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.cumulative_average = ctk.CTkCheckBox(
            self.frame,
            text="Cumulative Average",
        )
        self.cumulative_average.grid(row=3,
                                     column=0,
                                     padx=10,
                                     pady=5,
                                     sticky="w")
        self.auto_correlation = ctk.CTkCheckBox(self.frame,
                                                text="Auto Correlation")
        self.auto_correlation.grid(row=4,
                                   column=0,
                                   padx=10,
                                   pady=5,
                                   sticky="w")

        self.window_size = None
        self.running_average = ctk.CTkCheckBox(
            self.frame,
            text="Running Average",
            command=lambda: app.toggle_entry_state(
                self.running_average, self.window_size, default="10"))
        self.running_average.grid(row=5,
                                  column=0,
                                  padx=10,
                                  pady=5,
                                  sticky="w")
        self.window_size_label = ctk.CTkLabel(self.frame,
                                              text="Window Size:",
                                              anchor="w")
        self.window_size_label.grid(row=6,
                                    column=0,
                                    padx=10,
                                    pady=5,
                                    sticky="w")
        self.window_size = ctk.CTkEntry(
            self.frame,
            width=10,
            validate="key",
            validatecommand=(app.register(app.validate_number), "%P"),
        )
        self.window_size.grid(row=7,
                              column=0,
                              padx=10,
                              pady=5,
                              sticky="we")
        self.window_size.configure(state="disabled")

        app.settings_frame = self.frame
        app.settings_label = self.label
        app.mean = self.mean
        app.median = self.median
        app.cummulative_average = self.cumulative_average
        app.auto_correlation = self.auto_correlation
        app.running_average = self.running_average
        app.running_average_window_size_label = self.window_size_label
        app.window_size = self.window_size
