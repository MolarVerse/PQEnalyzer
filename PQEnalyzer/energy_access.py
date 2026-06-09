"""
Energy data access helpers built around PQAnalysis public attributes.

PQAnalysis exposes common energy columns as named arrays, while custom or
future columns may only be reachable through the generic ``info``/``data``
mapping. This module keeps that fallback in one place so plots and statistics
do not need to know PQAnalysis internals.
"""

from dataclasses import dataclass

import numpy as np


PARAMETER_ATTRIBUTES = {
    "SIMULATION-TIME": "simulation_time",
    "TEMPERATURE": "temperature",
    "PRESSURE": "pressure",
    "E(TOT)": "total_energy",
    "E(QM)": "qm_energy",
    "N(QM-ATOMS)": "number_of_qm_atoms",
    "E(KIN)": "kinetic_energy",
    "E(INTRA)": "intramolecular_energy",
    "VOLUME": "volume",
    "DENSITY": "density",
    "MOMENTUM": "momentum",
    "LOOPTIME": "looptime",
}
# Mapping from PQ info labels to PQAnalysis ``Energy`` attribute names.


@dataclass(frozen=True)
class EnergySeries:
    """
    Normalized view of a single energy parameter and its time axis.

    Attributes
    ----------
    time : np.ndarray
        Simulation-time values for the series.
    values : np.ndarray
        Numeric parameter values aligned with ``time``.
    label : str
        Original PQ info parameter label.
    unit : str
        Display unit for ``values``.
    """

    time: np.ndarray
    values: np.ndarray
    label: str
    unit: str


def parameter_values(energy, info_parameter: str) -> np.ndarray:
    """
    Return a parameter array, preferring PQAnalysis public Energy attributes.

    The fallback supports labels that are not represented in
    ``PARAMETER_ATTRIBUTES`` but are still present in the parsed PQAnalysis
    ``Energy`` object.
    """

    attribute = PARAMETER_ATTRIBUTES.get(info_parameter)
    if attribute is not None and hasattr(energy, attribute):
        return np.asarray(getattr(energy, attribute))

    return np.asarray(energy.data[energy.info[info_parameter]])


def parameter_unit(energy, info_parameter: str) -> str:
    """
    Return a parameter unit, preferring PQAnalysis public unit attributes.

    Unit lookup mirrors ``parameter_values`` so every caller receives the unit
    from the same source as the values when possible.
    """

    attribute = PARAMETER_ATTRIBUTES.get(info_parameter)
    unit_attribute = f"{attribute}_unit"
    if attribute is not None and hasattr(energy, unit_attribute):
        return getattr(energy, unit_attribute)

    return energy.units[info_parameter]


def simulation_time(energy) -> np.ndarray:
    """
    Return the simulation-time axis from a PQAnalysis Energy object.
    """

    return np.asarray(energy.simulation_time)


def series(energy, info_parameter: str) -> EnergySeries:
    """
    Return one file's normalized parameter series for plotting.
    """

    return EnergySeries(
        time=simulation_time(energy),
        values=parameter_values(energy, info_parameter),
        label=info_parameter,
        unit=parameter_unit(energy, info_parameter),
    )


def concatenate_time(energies: list) -> np.ndarray:
    """
    Concatenate simulation-time arrays from multiple energy files.
    """

    return np.concatenate([simulation_time(energy) for energy in energies])


def concatenate_parameter(energies: list, info_parameter: str) -> np.ndarray:
    """
    Concatenate one parameter from multiple energy files in reader order.
    """

    return np.concatenate(
        [parameter_values(energy, info_parameter) for energy in energies])


def concatenate_series(energies: list, info_parameter: str) -> EnergySeries:
    """
    Return one normalized parameter series across multiple energy files.

    Reader compatibility validation guarantees all files share the same unit,
    so the returned series can safely use the first file's unit.
    """

    return EnergySeries(
        time=concatenate_time(energies),
        values=concatenate_parameter(energies, info_parameter),
        label=info_parameter,
        unit=parameter_unit(energies[0], info_parameter),
    )


def difference_series(energies: list, info_parameter: str) -> EnergySeries:
    """
    Return the pointwise difference between two aligned energy series.

    The returned values are ``first - second``. Simulation-time axes must match
    exactly so the subtraction never hides shifted or differently sampled runs.
    """

    if len(energies) != 2:
        raise ValueError(
            "Difference plotting requires exactly two input files.")

    first = series(energies[0], info_parameter)
    second = series(energies[1], info_parameter)

    if (
        first.time.shape != second.time.shape
        or first.values.shape != second.values.shape
        or not np.array_equal(first.time, second.time)
    ):
        raise ValueError(
            "Difference plotting requires matching simulation-time axes.")

    return EnergySeries(
        time=first.time,
        values=first.values - second.values,
        label=info_parameter,
        unit=first.unit,
    )
