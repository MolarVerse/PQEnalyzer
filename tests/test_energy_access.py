import numpy as np
import pytest

from PQAnalysis.io import EnergyFileReader
from PQAnalysis.traj import MDEngineFormat

from PQEnalyzer.energy_access import (
    concatenate_parameter,
    concatenate_series,
    concatenate_time,
    difference_series,
    parameter_unit,
    parameter_values,
    series,
    simulation_time,
)
from PQEnalyzer.readers import BoxReader, Reader


class CustomEnergy:

    def __init__(self, values=None, time=None):
        if values is None:
            values = [10.0, 11.0, 12.0]
        if time is None:
            time = [1.0, 2.0, 3.0]
        self.info = {"CUSTOM": "CUSTOM"}
        self.units = {"CUSTOM": "arb"}
        self.data = {"CUSTOM": np.array(values)}
        self.simulation_time = np.array(time)


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


def test_difference_series_subtracts_two_aligned_series():
    first = CustomEnergy(values=[10.0, 11.0, 12.0])
    second = CustomEnergy(values=[1.0, 2.0, 3.0])

    energy_series = difference_series([first, second], "CUSTOM")

    np.testing.assert_array_equal(energy_series.time, [1.0, 2.0, 3.0])
    np.testing.assert_array_equal(energy_series.values, [9.0, 9.0, 9.0])
    assert energy_series.label == "CUSTOM"
    assert energy_series.unit == "arb"


def test_difference_series_requires_exactly_two_files():
    energy = CustomEnergy()

    with pytest.raises(ValueError, match="exactly two input files"):
        difference_series([energy], "CUSTOM")


def test_difference_series_requires_matching_time_axes():
    first = CustomEnergy(time=[1.0, 2.0, 3.0])
    second = CustomEnergy(time=[2.0, 3.0, 4.0])

    with pytest.raises(ValueError, match="matching simulation-time axes"):
        difference_series([first, second], "CUSTOM")


def test_difference_examples_have_nonconstant_difference():
    energies = Reader(
        ["examples/diff-run-a.en", "examples/diff-run-b.en"],
        MDEngineFormat.PQ,
    ).energies

    energy_series = difference_series(energies, "TEMPERATURE")

    np.testing.assert_array_equal(energy_series.time,
                                  np.arange(6, 16))
    assert len(np.unique(np.round(energy_series.values, decimals=6))) > 1


def test_energy_access_supports_box_reader_adapter():
    box_data = BoxReader(["examples/box-01.box"]).energies[0]

    np.testing.assert_array_equal(simulation_time(box_data),
                                  np.array([1, 2, 3, 4, 5]))
    np.testing.assert_allclose(parameter_values(box_data, "BOX-Y"),
                               np.array([22.0, 22.2, 22.4, 22.5, 22.7]))
    assert parameter_unit(box_data, "BOX-Y") == "A"

    box_series = series(box_data, "BOX-VOLUME")
    assert box_series.label == "BOX-VOLUME"
    assert box_series.unit == "A^3"
    assert box_series.values.shape == (5, )
