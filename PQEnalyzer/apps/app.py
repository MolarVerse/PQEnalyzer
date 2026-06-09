"""
This module contains the App class that is used to create the main application
window for the PQEnalyzer application.
"""

import signal

import customtkinter as ctk
import matplotlib.pyplot as plt

from .._logging import get_logger
from ..plots import PlotTime, PlotHistogram
from .app_layout import (
    build_parameter_selector,
    build_plot_controls,
    build_settings_controls,
    build_sidebar,
    configure_default_theme,
    configure_window,
)


logger = get_logger(__name__)


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
        configure_default_theme()
        configure_window(self)

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
        plt.close("all")
        self.quit()
        super().destroy()

    def build(self):
        """
        Build the main window.
        """
        build_sidebar(self, self.__change_appearance_mode_event)
        build_plot_controls(self, self.__plot_button_event,
                            self.__refresh_plots)
        build_parameter_selector(self, self.__change_info_event)
        build_settings_controls(self)

    def validate_number(self, value):
        """
        Validate if the input is a number.
        """
        if value in {"", "."}:
            return True

        try:
            return float(value) >= 0
        except ValueError:
            return False

    def toggle_entry_state(self, event, entry, default=""):
        """
        Toggle the state of the entry.
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
