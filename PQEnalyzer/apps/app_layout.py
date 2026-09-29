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

from ..preferences import PLOT_SCALE_LABELS, plot_scale_label
from ..plots.features import STATISTIC_FEATURES, TIME_SERIES_FEATURES


ICON_PATH = Path(__file__).resolve().parents[1] / "icons" / "icon.png"


def configure_default_theme(appearance_mode="System"):
    """
    Configure the persisted CustomTkinter theme.
    """

    # LOCAL-ONLY preview: PQ_FLAT_MONO=1 forces the flat-mono light theme.
    # The language is Gray-10 light-only, square, mono.
    try:
        from ..flat_mono import is_flat_mono_enabled

        if is_flat_mono_enabled():
            ctk.set_appearance_mode("Light")
            ctk.set_default_color_theme("blue")
            return
    except ImportError:
        pass

    ctk.set_appearance_mode(appearance_mode)
    ctk.set_default_color_theme("blue")


def _flat_mono_active():
    """Return True when the local flat-mono preview is requested."""
    try:
        from ..flat_mono import is_flat_mono_enabled

        return is_flat_mono_enabled()
    except ImportError:
        return False


def _flat_mono_font(size=13, weight="normal"):
    """Return a mono CTkFont for the flat-mono preview, else None."""
    if not _flat_mono_active():
        return None
    try:
        from ..flat_mono import FLAT_MONO_CTK

        family = FLAT_MONO_CTK["mono_font"][0]
    except (ImportError, KeyError):
        family = "IBM Plex Mono"
    return ctk.CTkFont(family=family, size=size, weight=weight)


def _style_flat_mono_widgets(widgets, primary_buttons=(), section_titles=()):
    """Apply square, hairline, mono styling (local preview only).

    ``primary_buttons`` marks Carbon primary actions (accent fill);
    other buttons render as secondary outlines. ``section_titles`` are
    labels restyled as uppercase group headings per the language.
    """
    if not _flat_mono_active():
        return
    try:
        from ..flat_mono import FLAT_MONO_CTK
    except ImportError:
        return
    for widget in widgets:
        if widget is None:
            continue
        try:
            if isinstance(widget, ctk.CTkFrame):
                widget.configure(
                    corner_radius=FLAT_MONO_CTK["corner_radius"],
                    fg_color=FLAT_MONO_CTK["surface"],
                    border_width=FLAT_MONO_CTK["border_width"],
                    border_color=FLAT_MONO_CTK["border"],
                )
            elif isinstance(widget, ctk.CTkButton):
                if widget in primary_buttons:
                    # Carbon primary: accent fill, white label.
                    widget.configure(
                        corner_radius=FLAT_MONO_CTK["corner_radius"],
                        fg_color=FLAT_MONO_CTK["accent"],
                        hover_color=FLAT_MONO_CTK["accent_dark"],
                        text_color="#ffffff",
                        border_width=0,
                        height=32,
                        font=_flat_mono_font(size=13, weight="normal"),
                    )
                else:
                    # Carbon secondary: 1px outline, ink label.
                    widget.configure(
                        corner_radius=FLAT_MONO_CTK["corner_radius"],
                        fg_color="transparent",
                        hover_color=FLAT_MONO_CTK["accent_soft"],
                        text_color=FLAT_MONO_CTK["ink"],
                        border_width=FLAT_MONO_CTK["border_width"],
                        border_color=FLAT_MONO_CTK["border_strong"],
                        height=32,
                        font=_flat_mono_font(size=13, weight="normal"),
                    )
            elif isinstance(widget, ctk.CTkOptionMenu):
                widget.configure(
                    corner_radius=FLAT_MONO_CTK["corner_radius"],
                    fg_color=FLAT_MONO_CTK["surface_subtle"],
                    button_color=FLAT_MONO_CTK["surface_subtle"],
                    button_hover_color=FLAT_MONO_CTK["border"],
                    text_color=FLAT_MONO_CTK["ink"],
                    height=32,
                    font=_flat_mono_font(size=13),
                )
            elif isinstance(widget, ctk.CTkCheckBox):
                widget.configure(
                    corner_radius=FLAT_MONO_CTK["corner_radius"],
                    border_width=2,
                    border_color=FLAT_MONO_CTK["border_strong"],
                    fg_color=FLAT_MONO_CTK["accent"],
                    hover_color=FLAT_MONO_CTK["accent"],
                    checkmark_color="#ffffff",
                    text_color=FLAT_MONO_CTK["ink"],
                    checkbox_height=18,
                    checkbox_width=18,
                    font=_flat_mono_font(size=12),
                )
            elif isinstance(widget, ctk.CTkLabel):
                if widget in section_titles:
                    widget.configure(
                        font=_flat_mono_font(size=12, weight="bold"),
                        text_color=FLAT_MONO_CTK["muted"],
                    )
                    try:
                        widget.configure(text=str(widget.cget("text")).upper())
                    except (ValueError, TypeError, AttributeError):
                        pass
                else:
                    widget.configure(
                        font=_flat_mono_font(size=12),
                        text_color=FLAT_MONO_CTK["ink_soft"],
                    )
            elif isinstance(widget, ctk.CTkEntry):
                widget.configure(
                    corner_radius=FLAT_MONO_CTK["corner_radius"],
                    fg_color=FLAT_MONO_CTK["surface"],
                    border_width=FLAT_MONO_CTK["border_width"],
                    border_color=FLAT_MONO_CTK["border_strong"],
                    text_color=FLAT_MONO_CTK["ink"],
                    height=32,
                    font=_flat_mono_font(size=13),
                )
        except (ValueError, TypeError, AttributeError):
            continue


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
    # LOCAL-ONLY flat-mono preview: nudge the fixed window to its content
    # size after the toolkit settles. Tiling compositors may otherwise show
    # a clipped window; this only ever grows toward Tk's requested size.
    if _flat_mono_active():
        def _fit_to_content():
            try:
                app.update_idletasks()
                req_w = app.winfo_reqwidth()
                req_h = app.winfo_reqheight()
                if req_w > app.winfo_width() or req_h > app.winfo_height():
                    app.geometry(f"{max(req_w, app.winfo_width())}"
                                 f"x{max(req_h, app.winfo_height())}")
            except (ValueError, TypeError, AttributeError):
                pass

        try:
            app.after(1000, _fit_to_content)
            app.after(3000, _fit_to_content)
        except (ValueError, TypeError, AttributeError):
            pass


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

    def __init__(
        self,
        app,
        change_appearance_mode_callback,
        change_plot_scale_callback,
    ):
        self.app = app
        self.change_appearance_mode_callback = change_appearance_mode_callback
        self.change_plot_scale_callback = change_plot_scale_callback

        self.frame = ctk.CTkFrame(app, width=140, corner_radius=0)
        self.frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.frame.grid_rowconfigure(4, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        # LOCAL-ONLY flat-mono: Gray-10 sidebar, hairline, mono.
        if _flat_mono_active():
            try:
                from ..flat_mono import FLAT_MONO_CTK

                self.frame.configure(
                    fg_color=FLAT_MONO_CTK["surface"],
                    border_width=FLAT_MONO_CTK["border_width"],
                    border_color=FLAT_MONO_CTK["border"],
                )
            except ImportError:
                pass

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
            font=_flat_mono_font(size=20, weight="bold")
            or ctk.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.grid(row=1, column=0, padx=10, pady=10)
        if _flat_mono_active():
            try:
                from ..flat_mono import FLAT_MONO_CTK

                self.logo_label.configure(text_color=FLAT_MONO_CTK["ink"])
            except ImportError:
                pass

        self.plot_scale_label = ctk.CTkLabel(
            self.frame,
            text="Plot Size:",
            anchor="w",
        )
        self.plot_scale_label.grid(
            row=5,
            column=0,
            padx=20,
            pady=(10, 0),
        )
        self.plot_scale_optionemenu = ctk.CTkOptionMenu(
            self.frame,
            values=list(PLOT_SCALE_LABELS),
            command=change_plot_scale_callback,
        )
        self.plot_scale_optionemenu.grid(
            row=6,
            column=0,
            padx=20,
            pady=(10, 10),
        )
        self.plot_scale_optionemenu.set(
            plot_scale_label(getattr(app, "plot_scale", 1.0)))

        self.appearance_mode_label = ctk.CTkLabel(
            self.frame,
            text="Appearance Mode:",
            anchor="w",
        )
        self.appearance_mode_label.grid(row=7,
                                        column=0,
                                        padx=20,
                                        pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self.frame,
            values=["System", "Light", "Dark"],
            command=change_appearance_mode_callback,
        )
        self.appearance_mode_optionemenu.grid(row=8,
                                              column=0,
                                              padx=20,
                                              pady=(10, 10))
        self.appearance_mode_optionemenu.set(
            getattr(app, "appearance_mode_setting", "System"))

        app.sidebar_frame = self.frame
        app.logo = self.logo
        app.sidebar_image_label = self.image_label
        app.logo_label = self.logo_label
        app.plot_scale_optionemenu = self.plot_scale_optionemenu
        app.appearance_mode_label = self.appearance_mode_label
        app.appearance_mode_optionemenu = self.appearance_mode_optionemenu
        # LOCAL-ONLY flat-mono preview styling.
        _style_flat_mono_widgets([
            self.plot_scale_label,
            self.plot_scale_optionemenu,
            self.appearance_mode_label,
            self.appearance_mode_optionemenu,
        ])


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
        plot_options_callback=None,
    ):
        self.app = app
        self.plot_button_callback = plot_button_callback
        self.auto_refresh_callback = auto_refresh_callback
        self.plot_options_callback = plot_options_callback

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
            text="Hide Raw Data",
            variable=self.plot_main_data,
            command=plot_options_callback,
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
        # LOCAL-ONLY flat-mono preview styling (Plot is the primary action).
        _style_flat_mono_widgets([
            self.frame,
            self.auto_refresh_checkbox,
            self.no_data_checkbox,
            self.auto_refresh_status_label,
            self.plot_button,
            self.histogram_button,
            self.dashboard_button,
        ], primary_buttons=(self.plot_button,))


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
            width=210,
            anchor="c",
        )
        self.optionmenu.grid(row=1, column=1, padx=20, pady=10)
        change_info_callback(app.info[0])

        app.info_frame = self.frame
        app.info_label = self.label
        app.info_optionmenu = self.optionmenu
        # LOCAL-ONLY flat-mono preview styling.
        _style_flat_mono_widgets([self.frame, self.label, self.optionmenu])


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
        self.window_size.bind("<KeyRelease>",
                              self.__window_size_changed)
        self.window_size.configure(state="disabled")

        app.settings_frame = self.frame
        app.statistics_frame = self.statistics_frame
        app.time_series_frame = self.time_series_frame
        app.settings_label = self.label
        app.time_series_label = self.time_series_label
        app.running_average_window_size_label = self.window_size_label
        app.window_size = self.window_size
        # LOCAL-ONLY flat-mono preview styling.
        _style_flat_mono_widgets([
            self.frame,
            self.statistics_frame,
            self.time_series_frame,
            self.label,
            self.time_series_label,
            self.window_size_label,
            self.window_size,
            *self.feature_controls.values(),
        ], section_titles=(self.label, self.time_series_label))

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

    def __window_size_changed(self, event=None):
        """
        Redraw the selected plot when the running-average window changes.
        """

        if self.statistics_changed_callback is not None:
            self.statistics_changed_callback()

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
