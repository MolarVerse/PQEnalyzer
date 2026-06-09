"""
Graphical CustomTkinter application coordinator.
"""

import signal

import customtkinter as ctk
import matplotlib.pyplot as plt

from .._logging import get_logger
from ..plots import PlotTime, PlotHistogram
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
        configure_window(self)

        self.reader = reader
        self.info = [
            *self.reader.energies[0].info
        ][1:]

        self.list_of_plots = []

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
        self.statistics_controls_view = StatisticsControlsView(self)

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

    def __change_info_event(self, new_info: str):
        """
        Store the currently selected energy parameter.
        """

        self.__selected_info = new_info

    def __refresh_plots(self):
        """
        Refresh open plots and forget plots whose windows were closed.
        """
        for plot in self.list_of_plots:

            if plot.figure.number not in plt.get_fignums():
                self.list_of_plots.remove(plot)
                continue

            plot.refresh()

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

        if interval is not None:
            plot.follow(self.__selected_info, interval)
        else:
            plot.simple(self.__selected_info)
