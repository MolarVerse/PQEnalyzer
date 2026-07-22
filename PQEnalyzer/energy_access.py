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


def has_parameter(energy, info_parameter: str) -> bool:
    """
    Return whether one parsed energy-like object exposes a parameter.
    """

    return info_parameter in getattr(energy, "info", {})


def energies_with_parameter(energies: list, info_parameter: str) -> list:
    """
    Return only the loaded energy-like objects that expose a parameter.
    """

    return [
        energy for energy in energies
        if has_parameter(energy, info_parameter)
    ]


def available_parameters(energies: list, *, include_time: bool = True) -> list:
    """
    Return the ordered union of parameters exposed by loaded files.
    """

    parameters = []
    seen = set()
    for energy in energies:
        for parameter in getattr(energy, "info", {}):
            if not include_time and parameter == "SIMULATION-TIME":
                continue
            if parameter in seen:
                continue
            seen.add(parameter)
            parameters.append(parameter)

    return parameters


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

    if not has_parameter(energy, info_parameter):
        raise ValueError(
            f"Parameter {info_parameter} is not present in this energy file.")

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

    if not has_parameter(energy, info_parameter):
        raise ValueError(
            f"Parameter {info_parameter} is not present in this energy file.")

    attribute = PARAMETER_ATTRIBUTES.get(info_parameter)
    unit_attribute = f"{attribute}_unit"
    if attribute is not None and hasattr(energy, unit_attribute):
        return getattr(energy, unit_attribute)

    return energy.units[info_parameter]


def parameter_unit_for_energies(energies: list, info_parameter: str) -> str:
    """
    Return a parameter unit from the first loaded file that exposes it.
    """

    matching_energies = energies_with_parameter(energies, info_parameter)
    if not matching_energies:
        raise ValueError(
            f"Parameter {info_parameter} is not present in any input file.")

    return parameter_unit(matching_energies[0], info_parameter)


def simulation_time(energy) -> np.ndarray:
    """
    Return the simulation-time axis from a PQAnalysis Energy object.
    """

    return np.asarray(energy.simulation_time)


def axis_label(energy) -> str:
    """
    Return the display label for an energy-like object's independent axis.
    """

    custom_label = getattr(energy, "axis_label", None)
    if custom_label:
        return custom_label

    time_unit = getattr(energy, "simulation_time_unit", None)
    if time_unit is None:
        time_unit = getattr(energy, "units", {}).get("SIMULATION-TIME")

    if time_unit == "step":
        return "Simulation Step"

    return "Simulation Time"


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
    Concatenate one parameter from files that expose it in reader order.
    """

    matching_energies = energies_with_parameter(energies, info_parameter)
    if not matching_energies:
        raise ValueError(
            f"Parameter {info_parameter} is not present in any input file.")

    return np.concatenate(
        [
            parameter_values(energy, info_parameter)
            for energy in matching_energies
        ])


def concatenate_series(energies: list, info_parameter: str) -> EnergySeries:
    """
    Return one normalized parameter series across multiple energy files.

    Files that do not expose the selected parameter are omitted. Reader
    compatibility validation guarantees common parameters use the same unit, so
    the returned series can safely use the first matching file's unit.
    """

    matching_energies = energies_with_parameter(energies, info_parameter)
    if not matching_energies:
        raise ValueError(
            f"Parameter {info_parameter} is not present in any input file.")

    return EnergySeries(
        time=concatenate_time(matching_energies),
        values=concatenate_parameter(energies, info_parameter),
        label=info_parameter,
        unit=parameter_unit(matching_energies[0], info_parameter),
    )


def difference_series(energies: list, info_parameter: str) -> EnergySeries:
    """
    Return the pointwise difference between two energy series.

    The returned values are ``first - second`` on shared simulation-time
    values. This lets users compare runs that overlap without requiring both
    files to start and stop at exactly the same step.
    """

    if len(energies) != 2:
        raise ValueError(
            "Difference plotting requires exactly two input files.")

    if not all(has_parameter(energy, info_parameter) for energy in energies):
        raise ValueError(
            "Difference plotting requires the selected parameter in both "
            "input files.")

    first = series(energies[0], info_parameter)
    second = series(energies[1], info_parameter)
    axis_name = axis_label(energies[0]).lower().replace(" ", "-")

    if (
        first.time.shape != first.values.shape
        or second.time.shape != second.values.shape
    ):
        raise ValueError(
            f"Difference plotting requires one value per {axis_name} point."
        )

    _, first_indices, second_indices = np.intersect1d(
        first.time,
        second.time,
        assume_unique=False,
        return_indices=True,
    )
    if first_indices.size == 0:
        raise ValueError(
            f"Difference plotting requires shared {axis_name} values.")

    first_order = np.argsort(first_indices)
    first_indices = first_indices[first_order]
    second_indices = second_indices[first_order]

    return EnergySeries(
        time=first.time[first_indices],
        values=first.values[first_indices] - second.values[second_indices],
        label=info_parameter,
        unit=first.unit,
    )
