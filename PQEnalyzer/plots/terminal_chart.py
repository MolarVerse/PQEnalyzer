"""
Terminal chart rendering for the Textual TUI.
"""

import plotext as plt

from ..energy_access import parameter_unit, series
from .features import iter_time_series_overlays
from .labels import unique_path_labels


def build_terminal_chart(reader, info_parameter, width=88, height=22,
                         options=None):
    """
    Return a plotext chart for one parameter as ANSI text.
    """

    plt.clear_figure()
    plt.plot_size(max(32, int(width)), max(8, int(height)))

    if options is None or not options.plot_main:
        labels = unique_path_labels(reader.filenames)
        for index, energy in enumerate(reader.energies):
            energy_series = series(energy, info_parameter)
            plt.plot(
                energy_series.time,
                energy_series.values,
                label=labels[index],
            )

    if options is not None:
        for overlay in iter_time_series_overlays(
            reader.energies,
            info_parameter,
            options,
            window_policy="clamp",
        ):
            plt.plot(
                overlay.time,
                overlay.values,
                label=overlay.label,
            )

    unit = parameter_unit(reader.energies[0], info_parameter)
    plt.title(f"{info_parameter} / {unit}")
    plt.xlabel("Simulation Time")
    plt.ylabel(f"{info_parameter} / {unit}")

    chart = plt.build()
    plt.clear_figure()
    return chart
