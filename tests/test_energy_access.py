import numpy as np

from PQAnalysis.io import EnergyFileReader
from PQAnalysis.traj import MDEngineFormat

from PQEnalyzer.energy_access import (
    concatenate_parameter,
    concatenate_series,
    concatenate_time,
    parameter_unit,
    parameter_values,
    series,
    simulation_time,
)


class CustomEnergy:

    def __init__(self):
        self.info = {"CUSTOM": "CUSTOM"}
        self.units = {"CUSTOM": "arb"}
        self.data = {"CUSTOM": np.array([10.0, 11.0, 12.0])}
        self.simulation_time = np.array([1.0, 2.0, 3.0])


def read_energy(filename):
    return EnergyFileReader(filename,
                            engine_format=MDEngineFormat.PQ).read()


def test_parameter_access_prefers_pqanalysis_public_attributes():
    energy = read_energy("tests/data/md-02.en")

    np.testing.assert_array_equal(parameter_values(energy, "TEMPERATURE"),
                                  energy.temperature)
    assert parameter_unit(energy, "TEMPERATURE") == energy.temperature_unit

    energy_series = series(energy, "TEMPERATURE")
    np.testing.assert_array_equal(energy_series.time,
                                  energy.simulation_time)
    np.testing.assert_array_equal(energy_series.values, energy.temperature)
    assert energy_series.label == "TEMPERATURE"
    assert energy_series.unit == energy.temperature_unit


def test_parameter_access_keeps_custom_parameter_fallback():
    energy = CustomEnergy()

    np.testing.assert_array_equal(parameter_values(energy, "CUSTOM"),
                                  np.array([10.0, 11.0, 12.0]))
    assert parameter_unit(energy, "CUSTOM") == "arb"
    np.testing.assert_array_equal(simulation_time(energy),
                                  np.array([1.0, 2.0, 3.0]))


def test_concatenate_helpers_join_series_from_multiple_energy_files():
    energies = [
        read_energy("tests/data/md-01.en"),
        read_energy("tests/data/md-02.en"),
    ]

    np.testing.assert_array_equal(concatenate_time(energies),
                                  np.arange(1, 11))
    np.testing.assert_array_equal(
        concatenate_parameter(energies, "SIMULATION-TIME"),
        np.arange(1, 11),
    )

    energy_series = concatenate_series(energies, "SIMULATION-TIME")
    np.testing.assert_array_equal(energy_series.time, np.arange(1, 11))
    np.testing.assert_array_equal(energy_series.values, np.arange(1, 11))
    assert energy_series.label == "SIMULATION-TIME"
    assert energy_series.unit == "ps"
