import pytest
import os

from PQAnalysis.traj import MDEngineFormat
from PQAnalysis.physical_data import EnergyError

from PQEnalyzer.readers import Reader


class TestReader:
    """
    Test the read_energy_files function.
    """

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test__init__(self, example_dir):
        assert os.path.exists(example_dir + "md-01.en")
        assert os.path.exists(example_dir + "md-02.en")
        assert os.path.exists(example_dir + "md-03.en")
        assert os.path.exists(example_dir + "md-01.info")
        assert os.path.exists(example_dir + "md-02.info")
        assert os.path.exists(example_dir + "md-03.info")

        assert os.path.isfile(example_dir + "empty.en")
        assert os.path.isfile(example_dir + "empty.info")

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_single_input(self, example_dir):
        list_filenames = [example_dir + "md-01.en"]

        reader = Reader(list_filenames, MDEngineFormat.PQ)
        assert len(reader.energies) == 1
        energy = reader.energies[0]
        assert len(energy.info) == 10

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_multiple_inputs(self, example_dir):
        list_filenames = [example_dir + "md-02.en", example_dir + "md-03.en"]

        energy_files = Reader(list_filenames, MDEngineFormat.PQ).energies
        assert len(energy_files) == 2
        energy = energy_files[0]
        assert len(energy.info) == 12
        energy = energy_files[1]
        assert len(energy.info) == 12

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_multiple_input_with_error(self, example_dir):
        list_filenames = [example_dir + "md-01.en", example_dir + "md-02.en"]

        with pytest.raises(ValueError):
            Reader(list_filenames, MDEngineFormat.PQ)

    def test_empty_input(self):
        list_filenames = []

        with pytest.raises(ValueError):
            Reader(list_filenames, MDEngineFormat.PQ)

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_empty_file(self, example_dir):
        list_filenames = [example_dir + "empty.en"]

        with pytest.raises(EnergyError):
            Reader(list_filenames, MDEngineFormat.PQ)

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_read_last(self, example_dir):
        list_filenames = [example_dir + "md-02.en", example_dir + "md-03.en"]

        reader = Reader(list_filenames, MDEngineFormat.PQ)
        energies = reader.energies
        energy1, energy2 = energies

        reader.read_last()
        assert energies == reader.energies
        assert energy1 == reader.energies[0]
        assert energy2 != reader.energies[1]
