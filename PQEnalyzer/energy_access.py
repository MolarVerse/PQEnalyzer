"""
Helpers for reading PQAnalysis energy data through its public API.
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


@dataclass(frozen=True)
class EnergySeries:
    """
    Normalized view of a single energy parameter and its time axis.
    """

    time: np.ndarray
    values: np.ndarray
    label: str
    unit: str


def parameter_values(energy, info_parameter: str) -> np.ndarray:
    """
    Return a parameter array, preferring PQAnalysis public Energy attributes.
    """

    attribute = PARAMETER_ATTRIBUTES.get(info_parameter)
    if attribute is not None and hasattr(energy, attribute):
        return np.asarray(getattr(energy, attribute))

    return np.asarray(energy.data[energy.info[info_parameter]])


def parameter_unit(energy, info_parameter: str) -> str:
    """
    Return a parameter unit, preferring PQAnalysis public unit attributes.
    """

    attribute = PARAMETER_ATTRIBUTES.get(info_parameter)
    unit_attribute = f"{attribute}_unit"
    if attribute is not None and hasattr(energy, unit_attribute):
        return getattr(energy, unit_attribute)

    return energy.units[info_parameter]


def simulation_time(energy) -> np.ndarray:
    """
    Return the simulation time axis from a PQAnalysis Energy object.
    """

    return np.asarray(energy.simulation_time)


def series(energy, info_parameter: str) -> EnergySeries:
    """
    Return a normalized parameter series for plotting.
    """

    return EnergySeries(
        time=simulation_time(energy),
        values=parameter_values(energy, info_parameter),
        label=info_parameter,
        unit=parameter_unit(energy, info_parameter),
    )


def concatenate_time(energies: list) -> np.ndarray:
    """
    Concatenate simulation time arrays from multiple energy files.
    """

    return np.concatenate([simulation_time(energy) for energy in energies])


def concatenate_parameter(energies: list, info_parameter: str) -> np.ndarray:
    """
    Concatenate one parameter from multiple energy files.
    """

    return np.concatenate(
        [parameter_values(energy, info_parameter) for energy in energies])


def concatenate_series(energies: list, info_parameter: str) -> EnergySeries:
    """
    Return one normalized parameter series across multiple energy files.
    """

    return EnergySeries(
        time=concatenate_time(energies),
        values=concatenate_parameter(energies, info_parameter),
        label=info_parameter,
        unit=parameter_unit(energies[0], info_parameter),
    )
