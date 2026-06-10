import numpy as np
import pytest
from PQAnalysis.core.cell import Cell

from PQEnalyzer.readers import BoxReader
from PQEnalyzer.readers.box_reader import BoxData


def test_box_reader_exposes_box_parameters_from_pqanalysis():
    reader = BoxReader(["examples/box-01.box"])

    assert reader.filenames == ["examples/box-01.box"]
    assert len(reader.energies) == 1

    box_data = reader.energies[0]
    assert list(box_data.info) == [
        "SIMULATION-TIME",
        "BOX-X",
        "BOX-Y",
        "BOX-Z",
        "ALPHA",
        "BETA",
        "GAMMA",
        "BOX-VOLUME",
    ]
    assert box_data.units == {
        "SIMULATION-TIME": "step",
        "BOX-X": "A",
        "BOX-Y": "A",
        "BOX-Z": "A",
        "ALPHA": "deg",
        "BETA": "deg",
        "GAMMA": "deg",
        "BOX-VOLUME": "A^3",
    }

    np.testing.assert_array_equal(box_data.simulation_time,
                                  np.array([1, 2, 3, 4, 5]))
    np.testing.assert_allclose(box_data.data["BOX-X"],
                               np.array([21.0, 21.1, 21.3, 21.5, 21.8]))
    np.testing.assert_allclose(box_data.data["GAMMA"],
                               np.array([90.0, 90.0, 90.1, 90.2, 90.1]))

    expected_volume = Cell(21.0, 22.0, 23.0, 90.0, 90.0, 90.0).volume
    assert box_data.data["BOX-VOLUME"][0] == pytest.approx(expected_volume)


def test_box_reader_supports_multiple_files_and_refresh():
    reader = BoxReader(["examples/box-01.box", "examples/box-02.box"])
    original_first = reader.energies[0]
    original_last = reader.energies[-1]

    reader.read_last()

    assert reader.energies[0] is original_first
    assert reader.energies[-1] is not original_last
    np.testing.assert_allclose(reader.energies[-1].data["BOX-Y"],
                               np.array([22.1, 22.0, 22.3, 22.6, 22.8]))


def test_box_reader_rejects_empty_input():
    with pytest.raises(ValueError, match="list of filenames is empty"):
        BoxReader([])


def test_box_data_from_pqanalysis_preserves_source_arrays():
    steps = np.array([10, 20])
    lengths = np.array([[2.0, 3.0, 4.0], [2.5, 3.5, 4.5]])
    angles = np.array([[90.0, 90.0, 90.0], [91.0, 89.0, 90.5]])

    box_data = BoxData.from_pqanalysis(steps, lengths, angles)

    assert box_data.steps is steps
    assert box_data.box_lengths is lengths
    assert box_data.box_angles is angles
    np.testing.assert_array_equal(box_data.data["SIMULATION-TIME"], steps)
    np.testing.assert_array_equal(box_data.data["BOX-Z"], lengths[:, 2])
    np.testing.assert_array_equal(box_data.data["BETA"], angles[:, 1])
