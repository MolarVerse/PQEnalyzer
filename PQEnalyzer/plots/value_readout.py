"""
Readout helpers for presenting plotted values outside the data area.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ValueReadoutEntry:
    """
    One row in a plot value readout.
    """

    label: str
    value: float
    color: str
    unit: str = ""
    linestyle: str = "-"

    @property
    def formatted_value(self) -> str:
        """
        Return the value formatted for a compact plot readout.
        """

        return format_readout_value(self.value, self.unit)


def format_readout_value(value, unit="") -> str:
    """
    Format a numeric value without forcing scientific notation unnecessarily.
    """

    if not np.isfinite(value):
        text = "n/a"
    else:
        magnitude = abs(value)
        if magnitude != 0 and (magnitude < 1e-3 or magnitude >= 1e5):
            text = f"{value:.4e}"
        else:
            text = f"{value:.5g}"

    return f"{text} {unit}".rstrip()


def latest_value_label(label, values, unit="") -> str:
    """
    Return a legend label that includes the latest finite value.
    """

    values = np.asarray(values, dtype=float)
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        return label

    return f"{label} ({format_readout_value(finite_values[-1], unit)})"
