"""
Graphical CustomTkinter application coordinator.
"""

import math
import signal

import customtkinter as ctk
import matplotlib.pyplot as plt

from .._logging import get_logger
from ..energy_access import available_parameters
from ..preferences import (
    PLOT_SIZE_KEYS,
    adjusted_plot_scale,
    load_preferences,
    plot_scale_from_label,
    plot_scale_label,
    save_preferences,
)
from ..plots import PlotDashboard, PlotTime, PlotHistogram
from ..plots.features import PLOT_FEATURES
from ..plots.options import PlotOptions
from ..plots.theme import apply_matplotlib_theme, resolve_appearance_mode
from .file_watcher import FileChangeWatcher
from .app_layout import (
    configure_default_theme,
    configure_window,
    ParameterSelectorView,
    PlotControlsView,
    SidebarView,
    StatisticsControlsView,
)


logger = get_logger(__name__)


class App(ctk.CTk):
    """
    Root GUI window that coordinates views, callbacks and plotting.

    Layout is delegated to view classes in ``app_layout``. This class keeps the
    mutable application state and event handlers that those views wire into
    widgets.

    Attributes
    ----------
    reader : Reader
        The reader object that contains the data.

    Methods
    -------
    build()
        Create the GUI view objects and attach their widgets.
    """

    def __init__(self, reader=None):
        """
        Initialize the root window and derive selectable parameters.
        """
        self.preferences = load_preferences()
        self.appearance_mode_setting = self.preferences.appearance_mode
        self.plot_scale = self.preferences.plot_scale
        configure_default_theme(self.appearance_mode_setting)
        super().__init__()
        self.appearance_mode = resolve_appearance_mode(
            self.appearance_mode_setting)
        apply_matplotlib_theme(self.appearance_mode, self.plot_scale)
        configure_window(self)

        self.reader = reader
        self.info = available_parameters(
            self.reader.energies,
            include_time=False,
        )

        self.list_of_plots = []
        self.selected_plot = None
        self.__syncing_plot_controls = False
        self.__restoring_preferences = False
        self.__file_watcher = None
        self.__auto_refresh_after_id = None
        self.__preferences_after_id = None

        signal.signal(signal.SIGINT,
                      lambda sig, frame: self.destroy())

    def destroy(self):
        """
        Destroy the app.
        """
        if "preferences" in self.__dict__:
            preferences_after_id = self.__dict__.get(
                "_App__preferences_after_id")
            if preferences_after_id is not None:
                self.after_cancel(preferences_after_id)
                self.__preferences_after_id = None
            self.__write_preferences()

        self.__stop_file_watcher()
        plt.close("all")
        self.quit()
        super().destroy()

    def build(self):
        """
        Create all view objects and attach their widgets to the root window.
        """
        if "preferences" in self.__dict__:
            self.__restoring_preferences = True
        self.sidebar_view = SidebarView(
            self,
            self.__change_appearance_mode_event,
            self.change_plot_scale,
        )
        self.plot_controls_view = PlotControlsView(
            self,
            self.__plot_button_event,
            self.__auto_refresh_control_event,
            self.__statistics_control_event,
        )
        self.parameter_selector_view = ParameterSelectorView(
            self, self.__change_info_event)
        self.statistics_controls_view = StatisticsControlsView(
            self, self.__statistics_control_event)
        if "preferences" in self.__dict__:
            self.__restore_preferences()
        if "auto_refresh" in self.__dict__:
            self.__auto_refresh_control_event()

    def validate_number(self, value):
        """
        Return whether a GUI entry value is empty or non-negative numeric text.
        """
        if value in {"", "."}:
            return True

        try:
            return float(value) >= 0
        except ValueError:
            return False

    def toggle_entry_state(self, event, entry, default=""):
        """
        Enable or disable a dependent entry based on a checkbox state.
        """
        entry.configure(state="normal")
        entry.delete(0, ctk.END)

        if event.get():
            entry.insert(0, default)
        else:
            entry.configure(state="disabled")

    def parse_positive_float(self, value, default, field_name):
        """
        Parse a positive float value from a GUI entry string.

        Empty values and a single decimal point use the supplied default so
        partially edited fields remain usable.
        """
        stripped_value = value.strip()

        if stripped_value in {"", "."}:
            return default

        parsed_value = float(stripped_value)
        if parsed_value <= 0:
            raise ValueError(f"{field_name} must be greater than zero.")

        return parsed_value

    def change_plot_scale(self, selection):
        """
        Apply and persist a plot typography preset.
        """

        if selection in {"increase", "decrease", "reset"}:
            plot_scale = adjusted_plot_scale(self.plot_scale, selection)
        else:
            plot_scale = plot_scale_from_label(selection)

        if plot_scale == self.plot_scale:
            return None

        self.plot_scale = plot_scale
        apply_matplotlib_theme(self.appearance_mode, plot_scale)

        scale_option = self.__dict__.get("plot_scale_optionemenu")
        if scale_option is not None:
            scale_option.set(plot_scale_label(plot_scale))

        self.__redraw_plots()
        self.__schedule_preferences_save()
        return None

    def plot_size(self, plot_kind, default):
        """
        Return the last window size for one plot kind.
        """

        return self.preferences.plot_sizes.get(plot_kind, default)

    def remember_plot_size(self, plot_kind, size):
        """
        Store a resized Matplotlib window for the next launch.
        """

        if plot_kind not in PLOT_SIZE_KEYS:
            raise ValueError(f"Unknown plot kind: {plot_kind}")

        width, height = (float(dimension) for dimension in size)
        if (
            not math.isfinite(width)
            or not math.isfinite(height)
            or width <= 0
            or height <= 0
        ):
            return None

        remembered_size = round(width, 2), round(height, 2)
        if self.preferences.plot_sizes.get(plot_kind) == remembered_size:
            return None

        self.preferences.plot_sizes[plot_kind] = remembered_size
        self.__schedule_preferences_save()
        return None

    def __change_appearance_mode_event(self, new_appearance_mode: str):
        """
        Apply a CustomTkinter appearance-mode selection.
        """

        self.appearance_mode_setting = new_appearance_mode
        ctk.set_appearance_mode(new_appearance_mode)
        self.appearance_mode = resolve_appearance_mode(new_appearance_mode)
        apply_matplotlib_theme(
            self.appearance_mode,
            self.__dict__.get("plot_scale", 1.0),
        )
        self.__redraw_plots()
        self.__schedule_preferences_save()

    def __change_info_event(self, new_info: str):
        """
        Store the currently selected energy parameter.
        """

        self.__selected_info = new_info
        self.__schedule_preferences_save()

    def __refresh_plots(self, show=True):
        """
        Refresh open plots and forget plots whose windows were closed.
        """
        selected_plot = self.__dict__.get("selected_plot")
        if (
            selected_plot is not None
            and selected_plot.figure.number in plt.get_fignums()
        ):
            selected_plot.options = PlotOptions.from_app(self)

        for plot in list(self.list_of_plots):

            if plot.figure.number not in plt.get_fignums():
                self.list_of_plots.remove(plot)
                if plot is self.__dict__.get("selected_plot"):
                    self.select_plot(None)
                continue

            plot.refresh(show=show)

    def __schedule_auto_refresh(self):
        """
        Debounce file-change events into one GUI-thread refresh.
        """

        if not self.auto_refresh.get():
            return None

        if self.__auto_refresh_after_id is not None:
            self.after_cancel(self.__auto_refresh_after_id)

        self.__auto_refresh_after_id = self.after(
            250,
            self.__auto_refresh_plots,
        )

        return None

    def __auto_refresh_plots(self):
        """
        Refresh plots after a watched input file changes.
        """

        self.__auto_refresh_after_id = None
        self.__refresh_plots(show=False)

        return None

    def __auto_refresh_control_event(self):
        """
        Start or stop file watching from the Auto-Refresh checkbox.
        """

        if self.auto_refresh.get():
            if self.__start_file_watcher():
                status = "Watching for file changes"
                if getattr(self.__file_watcher, "mode", None) == "polling":
                    status += " (polling)"
                self.__set_auto_refresh_status(status)
        else:
            self.__stop_file_watcher()
            self.__set_auto_refresh_status("Auto-refresh paused")

        self.__schedule_preferences_save()
        return None

    def __start_file_watcher(self):
        """
        Start watching the currently loaded files.
        """

        if self.__file_watcher is not None:
            return True

        watcher = FileChangeWatcher(
            self.reader.filenames,
            self.__schedule_auto_refresh,
        )
        if watcher.start():
            self.__file_watcher = watcher
            return True
        else:
            self.__set_checkbox(self.auto_refresh, False)
            self.__set_auto_refresh_status("Auto-refresh unavailable")

        return False

    def __stop_file_watcher(self):
        """
        Stop the active file watcher, if any.
        """

        if self.__dict__.get("_App__auto_refresh_after_id") is not None:
            self.after_cancel(self.__auto_refresh_after_id)
            self.__auto_refresh_after_id = None

        if self.__dict__.get("_App__file_watcher") is None:
            return None

        self.__file_watcher.stop()
        self.__file_watcher = None

        return None

    def __set_auto_refresh_status(self, message):
        """
        Update the Auto-Refresh status label when the view exists.
        """

        status_label = self.__dict__.get("auto_refresh_status_label")
        if status_label is not None:
            status_label.configure(text=message)

    def __redraw_plots(self):
        """
        Redraw open plots after visual-only GUI setting changes.
        """
        for plot in list(self.list_of_plots):

            if plot.figure.number not in plt.get_fignums():
                self.list_of_plots.remove(plot)
                if plot is self.__dict__.get("selected_plot"):
                    self.select_plot(None)
                continue

            plot.redraw()

    def __plot_button_event(self, event):
        """
        Create a time-series or histogram plot from the current GUI state.

        Parameters
        ----------
        event : int
            Plot selector: ``0`` creates a time plot, ``1`` creates a
            histogram plot.
        """

        if event == 0:
            plot_factory = PlotTime
        elif event == 1:
            plot_factory = PlotHistogram
        elif event == 2:
            plot_factory = PlotDashboard
        else:
            raise ValueError(f"Unknown plot event: {event}")

        plot = plot_factory(self)

        self.list_of_plots.append(plot)

        if event == 2:
            self.select_plot(None)
            info_parameter = None
        else:
            info_parameter = self.__selected_info

        plot.simple(info_parameter)

    def open_focus_plot(self, info_parameter):
        """
        Open a focused time-series plot for one dashboard parameter.
        """

        plot = PlotTime(self)
        self.list_of_plots.append(plot)

        plot.simple(info_parameter)

    def select_plot(self, plot):
        """
        Select a focused plot and mirror its options into the GUI controls.
        """

        if plot is not None and plot.figure.number not in plt.get_fignums():
            plot = None

        self.selected_plot = plot
        if plot is None:
            return

        self.__sync_plot_controls(plot.options)
        self.__schedule_preferences_save()

    def __statistics_control_event(self):
        """
        Apply changed statistic controls to the selected focused plot.
        """

        if self.__syncing_plot_controls:
            return None

        self.__schedule_preferences_save()
        if self.selected_plot is None:
            return None

        if self.selected_plot.figure.number not in plt.get_fignums():
            self.select_plot(None)
            return None

        self.selected_plot.redraw(options=PlotOptions.from_app(self))

    def __sync_plot_controls(self, options):
        """
        Update GUI statistic controls from one plot's stored options.
        """

        self.__syncing_plot_controls = True
        try:
            for feature in PLOT_FEATURES:
                self.__set_checkbox(
                    getattr(self, feature.option_attribute),
                    getattr(options, feature.option_attribute),
                )
            self.__set_checkbox(self.plot_main_data, options.plot_main)
            self.__set_entry(self.window_size, options.window_size)
            if options.running_average:
                self.window_size.configure(state="normal")
            else:
                self.window_size.configure(state="disabled")
        finally:
            self.__syncing_plot_controls = False

    def __set_checkbox(self, checkbox, value):
        """
        Set a checkbox-like widget without invoking its command.
        """

        if value:
            if hasattr(checkbox, "select"):
                checkbox.select()
            else:
                checkbox.set(True)
        else:
            if hasattr(checkbox, "deselect"):
                checkbox.deselect()
            else:
                checkbox.set(False)

    def __set_entry(self, entry, value):
        """
        Replace the text of an entry-like widget.
        """

        entry.configure(state="normal")
        entry.delete(0, ctk.END)
        if value:
            entry.insert(0, value)

    def __restore_preferences(self):
        """
        Restore the last controls that are valid for the loaded files.
        """

        self.__restoring_preferences = True
        try:
            self.__set_checkbox(
                self.auto_refresh,
                self.preferences.auto_refresh,
            )
            self.__sync_plot_controls(
                PlotOptions.from_mapping(self.preferences.plot_options))

            selected_parameter = self.preferences.selected_parameter
            if selected_parameter in self.info:
                self.info_optionmenu.set(selected_parameter)
                self.__selected_info = selected_parameter

            self.plot_scale_optionemenu.set(
                plot_scale_label(self.plot_scale))
            self.appearance_mode_optionemenu.set(
                self.appearance_mode_setting)
        finally:
            self.__restoring_preferences = False

    def __schedule_preferences_save(self):
        """
        Debounce preference writes after GUI and plot changes.
        """

        if (
            "preferences" not in self.__dict__
            or getattr(self, "_App__restoring_preferences", False)
        ):
            return None

        preferences_after_id = self.__dict__.get(
            "_App__preferences_after_id")
        if preferences_after_id is not None:
            self.after_cancel(preferences_after_id)

        self.__preferences_after_id = self.after(
            300,
            self.__write_preferences,
        )
        return None

    def __capture_preferences(self):
        """
        Copy the current widgets into the persistent preference object.
        """

        self.preferences.appearance_mode = self.appearance_mode_setting
        self.preferences.plot_scale = self.plot_scale
        self.preferences.selected_parameter = self.__dict__.get(
            "_App__selected_info")

        if "auto_refresh" in self.__dict__:
            self.preferences.auto_refresh = bool(self.auto_refresh.get())

        required_options = [
            "plot_main_data",
            "window_size",
            *(feature.option_attribute for feature in PLOT_FEATURES),
        ]
        if all(option in self.__dict__ for option in required_options):
            self.preferences.plot_options = (
                PlotOptions.from_app(self).to_mapping())

    def __write_preferences(self):
        """
        Persist the latest user settings immediately.
        """

        self.__preferences_after_id = None
        self.__capture_preferences()
        return save_preferences(self.preferences)
