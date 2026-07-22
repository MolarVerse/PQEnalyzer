import numpy as np
import pytest

from PQAnalysis.io import EnergyFileReader
from PQAnalysis.traj import MDEngineFormat

from PQEnalyzer.energy_access import (
    available_parameters,
    axis_label,
    concatenate_parameter,
    concatenate_series,
    concatenate_time,
    difference_series,
    energies_with_parameter,
    has_parameter,
    parameter_unit,
    parameter_unit_for_energies,
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


def test_energy_access_omits_files_missing_selected_parameter():
    energies = Reader(
        ["tests/data/md-01.en", "tests/data/md-02.en"],
        MDEngineFormat.PQ,
    ).energies

    assert has_parameter(energies[0], "VOLUME") is False
    assert has_parameter(energies[1], "VOLUME") is True
    assert energies_with_parameter(energies, "VOLUME") == [energies[1]]
    assert "VOLUME" in available_parameters(energies, include_time=False)
    assert "DENSITY" in available_parameters(energies, include_time=False)
    assert parameter_unit_for_energies(energies, "VOLUME") == "A^3"

    energy_series = concatenate_series(energies, "VOLUME")

    np.testing.assert_array_equal(energy_series.time, np.arange(6, 11))
    np.testing.assert_allclose(energy_series.values, energies[1].volume)
    assert energy_series.unit == "A^3"


def test_parameter_access_rejects_missing_parameter():
    energy = read_energy("tests/data/md-01.en")

    with pytest.raises(ValueError, match="not present"):
        parameter_values(energy, "VOLUME")

    with pytest.raises(ValueError, match="not present"):
        parameter_unit(energy, "VOLUME")


def test_collection_parameter_access_rejects_missing_parameter():
    energies = [CustomEnergy()]

    with pytest.raises(ValueError, match="not present in any input file"):
        parameter_unit_for_energies(energies, "MISSING")

    with pytest.raises(ValueError, match="not present in any input file"):
        concatenate_parameter(energies, "MISSING")

    with pytest.raises(ValueError, match="not present in any input file"):
        concatenate_series(energies, "MISSING")


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


def test_difference_series_requires_parameter_in_both_files():
    energies = Reader(
        ["tests/data/md-01.en", "tests/data/md-02.en"],
        MDEngineFormat.PQ,
    ).energies

    with pytest.raises(ValueError, match="selected parameter in both"):
        difference_series(energies, "VOLUME")


def test_difference_series_uses_shared_time_axis_values():
    first = CustomEnergy(time=[1.0, 2.0, 3.0, 4.0],
                         values=[10.0, 20.0, 30.0, 40.0])
    second = CustomEnergy(time=[3.0, 4.0, 5.0],
                          values=[1.0, 2.0, 3.0])

    energy_series = difference_series([first, second], "CUSTOM")

    np.testing.assert_array_equal(energy_series.time, [3.0, 4.0])
    np.testing.assert_array_equal(energy_series.values, [29.0, 38.0])


def test_difference_series_requires_shared_time_axis_values():
    first = CustomEnergy(time=[1.0, 2.0, 3.0])
    second = CustomEnergy(time=[4.0, 5.0, 6.0])

    with pytest.raises(ValueError, match="shared simulation-time values"):
        difference_series([first, second], "CUSTOM")


def test_difference_series_requires_values_aligned_to_time():
    first = CustomEnergy(time=[1.0, 2.0, 3.0],
                         values=[10.0, 20.0])
    second = CustomEnergy(time=[1.0, 2.0, 3.0],
                          values=[1.0, 2.0, 3.0])

    with pytest.raises(ValueError, match="one value per simulation-time"):
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


def test_difference_series_supports_box_reader_adapter():
    energies = BoxReader([
        "examples/box-01.box",
        "examples/box-02.box",
    ]).energies

    energy_series = difference_series(energies, "BOX-X")

    np.testing.assert_array_equal(energy_series.time,
                                  np.array([1, 2, 3, 4, 5]))
    np.testing.assert_allclose(
        energy_series.values,
        [0.1, 0.1, 0.1, -0.2, 0.2],
    )


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


def test_axis_label_uses_custom_label_when_available():
    energy = CustomEnergy()
    energy.axis_label = "Optimization Step"

    assert axis_label(energy) == "Optimization Step"


def test_axis_label_distinguishes_time_and_step_units():
    energy = CustomEnergy()
    assert axis_label(energy) == "Simulation Time"

    box_data = BoxReader(["examples/box-01.box"]).energies[0]
    assert axis_label(box_data) == "Simulation Step"
