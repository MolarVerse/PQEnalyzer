"""
Graphical CustomTkinter application coordinator.
"""

import signal

import customtkinter as ctk
import matplotlib.pyplot as plt

from .._logging import get_logger
from ..plots import PlotDashboard, PlotTime, PlotHistogram
from ..plots.options import PlotOptions
from ..plots.theme import apply_matplotlib_theme, resolve_appearance_mode
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
        super().__init__()
        configure_default_theme()
        self.appearance_mode = resolve_appearance_mode("System")
        apply_matplotlib_theme(self.appearance_mode)
        configure_window(self)

        self.reader = reader
        self.info = [
            *self.reader.energies[0].info
        ][1:]

        self.list_of_plots = []
        self.selected_plot = None
        self.__syncing_plot_controls = False

        signal.signal(signal.SIGINT,
                      lambda sig, frame: self.destroy())

    def destroy(self):
        """
        Destroy the app.
        """
        plt.close("all")
        self.quit()
        super().destroy()

    def build(self):
        """
        Create all view objects and attach their widgets to the root window.
        """
        self.sidebar_view = SidebarView(
            self, self.__change_appearance_mode_event)
        self.plot_controls_view = PlotControlsView(
            self, self.__plot_button_event, self.__refresh_plots)
        self.parameter_selector_view = ParameterSelectorView(
            self, self.__change_info_event)
        self.statistics_controls_view = StatisticsControlsView(
            self, self.__statistics_control_event)

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

    def __change_appearance_mode_event(self, new_appearance_mode: str):
        """
        Apply a CustomTkinter appearance-mode selection.
        """

        ctk.set_appearance_mode(new_appearance_mode)
        self.appearance_mode = resolve_appearance_mode(new_appearance_mode)
        apply_matplotlib_theme(self.appearance_mode)
        self.__redraw_plots()

    def __change_info_event(self, new_info: str):
        """
        Store the currently selected energy parameter.
        """

        self.__selected_info = new_info

    def __refresh_plots(self):
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

            plot.refresh()

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

        interval = None
        if self.follow.get():
            try:
                interval = self.parse_positive_float(
                    self.interval.get(), 1.0, "Interval")
            except ValueError as error:
                logger.warning("%s", error)
                return None

        plot = plot_factory(self)

        self.list_of_plots.append(plot)

        if event == 2:
            self.select_plot(None)
            info_parameter = None
        else:
            info_parameter = self.__selected_info

        if interval is not None:
            plot.follow(info_parameter, interval)
        else:
            plot.simple(info_parameter)

    def open_focus_plot(self, info_parameter):
        """
        Open a focused time-series plot for one dashboard parameter.
        """

        interval = None
        if self.follow.get():
            try:
                interval = self.parse_positive_float(
                    self.interval.get(), 1.0, "Interval")
            except ValueError as error:
                logger.warning("%s", error)
                return None

        self.__change_info_event(info_parameter)
        plot = PlotTime(self)
        self.list_of_plots.append(plot)

        if interval is not None:
            plot.follow(info_parameter, interval)
        else:
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

    def __statistics_control_event(self):
        """
        Apply changed statistic controls to the selected focused plot.
        """

        if self.__syncing_plot_controls:
            return None

        if self.difference.get():
            self.plot_main_data.set(True)

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
            self.__set_checkbox(self.mean, options.mean)
            self.__set_checkbox(self.median, options.median)
            self.__set_checkbox(
                self.cummulative_average,
                options.cummulative_average,
            )
            self.__set_checkbox(
                self.self_correlation_mean,
                options.self_correlation_mean,
            )
            self.__set_checkbox(self.difference, options.difference)
            self.__set_checkbox(self.running_average,
                                options.running_average)
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
