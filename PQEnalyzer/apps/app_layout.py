"""
View classes for the PQEnalyzer GUI layout.

Each view owns a focused group of CustomTkinter widgets and mirrors the widget
attributes onto ``App`` for compatibility with existing plotting code. This
keeps ``App`` as the coordinator while making layout sections independently
testable.
"""

import tkinter
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk

ICON_PATH = Path(__file__).resolve().parents[1] / "icons" / "icon.png"
from ..plots.features import STATISTIC_FEATURES, TIME_SERIES_FEATURES


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

    image = Image.open(ICON_PATH)
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
            Image.open(ICON_PATH),
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

    This view exposes plot state widgets on the app because ``Plot`` reads that
    state when a plot window is created or refreshed.
    """

    def __init__(
        self,
        app,
        plot_button_callback,
        auto_refresh_callback,
    ):
        self.app = app
        self.plot_button_callback = plot_button_callback
        self.auto_refresh_callback = auto_refresh_callback

        self.frame = ctk.CTkFrame(app, width=200)
        self.frame.grid(row=2,
                        column=1,
                        sticky="nsew",
                        padx=(20, 20),
                        pady=(10, 10))
        self.frame.grid_rowconfigure(4, weight=1)
        self.frame.grid_columnconfigure(2, weight=1)

        self.auto_refresh = tkinter.BooleanVar()
        self.auto_refresh.set(True)
        self.auto_refresh_checkbox = ctk.CTkCheckBox(
            master=self.frame,
            border_width=2,
            text="Auto-Refresh",
            variable=self.auto_refresh,
            command=auto_refresh_callback,
        )
        self.auto_refresh_checkbox.grid(row=0,
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

        self.auto_refresh_status_label = ctk.CTkLabel(
            self.frame,
            text="Watching for file changes",
            anchor="w",
        )
        self.auto_refresh_status_label.grid(row=1,
                                            column=0,
                                            columnspan=2,
                                            padx=10,
                                            pady=(0, 5),
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

        self.dashboard_button = ctk.CTkButton(
            master=self.frame,
            border_width=2,
            text="Live Monitor",
            command=lambda: plot_button_callback(2),
        )
        self.dashboard_button.grid(row=4,
                                   column=0,
                                   columnspan=2,
                                   padx=(10, 10),
                                   pady=(10, 10),
                                   sticky="nsew")

        app.plot_frame = self.frame
        app.auto_refresh = self.auto_refresh
        app.check_auto_refresh = self.auto_refresh_checkbox
        app.plot_main_data = self.plot_main_data
        app.check_nodata = self.no_data_checkbox
        app.auto_refresh_status_label = self.auto_refresh_status_label
        app.button_plot = self.plot_button
        app.button_hist = self.histogram_button
        app.button_dashboard = self.dashboard_button


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
    Statistics and time-series overlay controls.

    Plot classes read these checkboxes directly from ``App`` when they collect
    plotting options, so this view assigns the same attributes that older App
    code created inline.
    """

    def __init__(self, app, statistics_changed_callback=None):
        self.app = app
        self.statistics_changed_callback = statistics_changed_callback

        self.frame = ctk.CTkFrame(app, width=200)
        self.frame.grid(row=1,
                        column=1,
                        sticky="nsew",
                        padx=(20, 20),
                        pady=(10, 10))
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.statistics_frame = ctk.CTkFrame(self.frame)
        self.statistics_frame.grid(row=0,
                                   column=0,
                                   sticky="nsew",
                                   padx=0,
                                   pady=(0, 10))
        self.statistics_frame.grid_columnconfigure(0, weight=1)

        self.time_series_frame = ctk.CTkFrame(self.frame)
        self.time_series_frame.grid(row=1,
                                    column=0,
                                    sticky="nsew",
                                    padx=0,
                                    pady=0)
        self.time_series_frame.grid_rowconfigure(
            len(TIME_SERIES_FEATURES) + 4,
            weight=1,
        )
        self.time_series_frame.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(
            self.statistics_frame,
            text="Statistics:",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.feature_controls = {}
        for row, feature in enumerate(STATISTIC_FEATURES, start=1):
            self.__create_feature_control(
                self.statistics_frame,
                feature,
                row,
            )

        self.time_series_label = ctk.CTkLabel(
            self.time_series_frame,
            text="Time-series overlays:",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.time_series_label.grid(row=0,
                                    column=0,
                                    padx=10,
                                    pady=5,
                                    sticky="w")
        for row, feature in enumerate(TIME_SERIES_FEATURES, start=1):
            self.__create_feature_control(
                self.time_series_frame,
                feature,
                row,
            )

        self.window_size = None
        self.window_size_label = ctk.CTkLabel(self.time_series_frame,
                                              text="Window Size:",
                                              anchor="w")
        self.window_size_label.grid(row=len(TIME_SERIES_FEATURES) + 1,
                                    column=0,
                                    padx=10,
                                    pady=5,
                                    sticky="w")
        self.window_size = ctk.CTkEntry(
            self.time_series_frame,
            width=10,
            validate="key",
            validatecommand=(app.register(app.validate_number), "%P"),
        )
        self.window_size.grid(row=len(TIME_SERIES_FEATURES) + 2,
                              column=0,
                              padx=10,
                              pady=5,
                              sticky="we")
        self.window_size.configure(state="disabled")

        app.settings_frame = self.frame
        app.statistics_frame = self.statistics_frame
        app.time_series_frame = self.time_series_frame
        app.settings_label = self.label
        app.time_series_label = self.time_series_label
        app.running_average_window_size_label = self.window_size_label
        app.window_size = self.window_size

    def __create_feature_control(self, frame, feature, row):
        """
        Create one registry-backed checkbox and expose it on the app.
        """

        control = ctk.CTkCheckBox(
            frame,
            text=feature.label,
            command=self.__feature_command(feature),
        )
        control.grid(row=row, column=0, padx=10, pady=5, sticky="w")

        setattr(self, feature.gui_attribute, control)
        setattr(self.app, feature.option_attribute, control)
        self.feature_controls[feature.key] = control

    def __enable_no_data_for_difference(self, feature):
        """
        Hide raw series by default when plotting a derived difference.
        """

        if feature.key == "difference" and self.difference.get():
            self.app.plot_main_data.set(True)

    def __toggle_running_average_entry(self, feature):
        """
        Toggle the running-average window entry for the running-average feature.
        """

        if feature.key != "running_average":
            return

        self.app.toggle_entry_state(
            self.running_average,
            self.window_size,
            default="10",
        )

    def __feature_command(self, feature):
        """
        Return the GUI command for a registry-backed feature control.
        """

        def command():
            self.__enable_no_data_for_difference(feature)
            self.__toggle_running_average_entry(feature)
            if self.statistics_changed_callback is not None:
                self.statistics_changed_callback()

        return command
