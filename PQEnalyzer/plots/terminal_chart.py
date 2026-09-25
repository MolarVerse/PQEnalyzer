"""
Terminal chart rendering for the Textual TUI.
"""

import plotext as plt

from ..energy_access import (
    axis_label,
    has_parameter,
    parameter_unit_for_energies,
    series,
)
from .features import iter_time_series_overlays
from .labels import parameter_label, unique_path_labels
from .theme import series_rgb


def _appearance_for_terminal():
    """Return the palette key for terminal charts (local preview aware)."""
    try:
        from ..flat_mono import is_flat_mono_enabled

        if is_flat_mono_enabled():
            return "Light"
    except ImportError:
        pass
    return "Dark"


def build_terminal_chart(reader, info_parameter, width=88, height=22,
                         options=None):
    """
    Return a plotext chart for one parameter as ANSI text.
    """

    plt.clear_figure()
    plt.plot_size(max(32, int(width)), max(8, int(height)))
    appearance = _appearance_for_terminal()

    if options is None or not options.plot_main:
        labels = unique_path_labels(reader.filenames)
        for index, energy in enumerate(reader.energies):
            if not has_parameter(energy, info_parameter):
                continue

            energy_series = series(energy, info_parameter)
            plt.plot(
                energy_series.time,
                energy_series.values,
                label=labels[index],
                color=series_rgb(index, appearance),
            )

    if options is not None:
        overlays = iter_time_series_overlays(
            reader.energies,
            info_parameter,
            options,
            window_policy="clamp",
        )
        for overlay_index, overlay in enumerate(overlays):
            plt.plot(
                overlay.time,
                overlay.values,
                label=overlay.label,
                color=series_rgb(
                    len(reader.energies) + overlay_index,
                    appearance,
                ),
            )

    unit = parameter_unit_for_energies(reader.energies, info_parameter)
    label = parameter_label(info_parameter, unit)
    plt.title(label)
    plt.xlabel(axis_label(reader.energies[0]))
    plt.ylabel(label)

    chart = plt.build()
    plt.clear_figure()
    return chart
