import os
import shutil
from types import SimpleNamespace

import numpy as np
import pytest

from PQAnalysis.traj import MDEngineFormat
from PQAnalysis.physical_data import EnergyError

from PQEnalyzer.readers import Reader
from PQEnalyzer.readers import pq_energy
from PQEnalyzer.readers.pq_energy import (
    _normalize_energy_data_for_info,
    parse_single_column_pq_info_file,
    read_single_column_pq_energy_file,
)


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
    def test_single_column_pq_info_file(self, example_dir):
        list_filenames = [example_dir + "single-column-output.en"]

        reader = Reader(list_filenames, MDEngineFormat.PQ)

        assert len(reader.energies) == 1
        energy = reader.energies[0]
        assert len(energy.info) == 13
        assert energy.info["N(SM-MOL)"] == 10
        assert energy.units["N(SM-MOL)"] == "-"
        assert energy.info["MOMENTUM"] == 11
        assert energy.info["LOOPTIME"] == 12
        assert energy.data[energy.info["N(SM-MOL)"]][0] == 0

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_single_column_pq_info_file_normalizes_row_major_data(
            self, example_dir, monkeypatch):
        class RowMajorEnergyFileReader:
            def __init__(self, filename, use_info_file):
                self.filename = filename
                self.use_info_file = use_info_file

            def read(self):
                assert self.use_info_file is False
                return SimpleNamespace(data=np.arange(13).reshape((1, 13)))

        monkeypatch.setattr(pq_energy, "EnergyFileReader",
                            RowMajorEnergyFileReader)

        energy = read_single_column_pq_energy_file(
            example_dir + "single-column-output.en")

        assert energy.data.shape == (13, 1)
        assert energy.data[energy.info["N(SM-MOL)"]][0] == 10

    def test_single_column_pq_energy_reader_ignores_missing_info_file(
            self, tmp_path):
        energy_file = tmp_path / "missing-info.en"
        energy_file.write_text("1 2 3\n")

        assert read_single_column_pq_energy_file(energy_file) is None

    def test_normalize_single_column_pq_energy_data_handles_one_dimensional_data(
            self):
        data = _normalize_energy_data_for_info(np.arange(3), {
            0: 0,
            1: 1,
            2: 2,
        })

        assert data.shape == (3, 1)

    def test_normalize_single_column_pq_energy_data_keeps_column_major_data(
            self):
        data = _normalize_energy_data_for_info(np.zeros((3, 1)), {
            0: 0,
            1: 1,
            2: 2,
        })

        assert data.shape == (3, 1)

    def test_normalize_single_column_pq_energy_data_keeps_invalid_shape(self):
        data = _normalize_energy_data_for_info(np.zeros((2, 3)), {0: 0})

        assert data.shape == (2, 3)

    def test_single_column_pq_info_parser_rejects_invalid_rows(self, tmp_path):
        info_file = tmp_path / "invalid.info"
        info_file.write_text(
            "header\n"
            "header\n"
            "header\n"
            "| SIMULATION-TIME 1 ps TEMPERATURE 2 K |\n"
            "| invalid row |\n"
            "footer\n"
            "footer\n",
        )

        assert parse_single_column_pq_info_file(info_file) is None

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

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_multiple_input_with_different_parameters(self, tmp_path,
                                                      example_dir):
        reference = tmp_path / "reference"
        changed = tmp_path / "changed"
        shutil.copyfile(example_dir + "md-02.en", reference.with_suffix(".en"))
        shutil.copyfile(example_dir + "md-02.info",
                        reference.with_suffix(".info"))
        shutil.copyfile(example_dir + "md-02.en", changed.with_suffix(".en"))

        changed_info = (reference.with_suffix(".info").read_text().replace(
            "VOLUME", "BOX-VOLUME", 1))
        changed.with_suffix(".info").write_text(changed_info)

        with pytest.raises(ValueError, match="same info parameters"):
            Reader(
                [
                    str(reference.with_suffix(".en")),
                    str(changed.with_suffix(".en")),
                ],
                MDEngineFormat.PQ,
            )

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_multiple_input_with_different_units(self, tmp_path, example_dir):
        reference = tmp_path / "reference"
        changed = tmp_path / "changed"
        shutil.copyfile(example_dir + "md-02.en", reference.with_suffix(".en"))
        shutil.copyfile(example_dir + "md-02.info",
                        reference.with_suffix(".info"))
        shutil.copyfile(example_dir + "md-02.en", changed.with_suffix(".en"))

        changed_info = (reference.with_suffix(".info").read_text().replace(
            "A^3", "nm^3", 1))
        changed.with_suffix(".info").write_text(changed_info)

        with pytest.raises(ValueError, match="same units"):
            Reader(
                [
                    str(reference.with_suffix(".en")),
                    str(changed.with_suffix(".en")),
                ],
                MDEngineFormat.PQ,
            )

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

    @pytest.mark.parametrize("example_dir", ["tests/data/"], indirect=False)
    def test_read_last_rejects_incompatible_refresh(self, tmp_path,
                                                    example_dir):
        reference = tmp_path / "reference"
        changed = tmp_path / "changed"
        shutil.copyfile(example_dir + "md-02.en", reference.with_suffix(".en"))
        shutil.copyfile(example_dir + "md-02.info",
                        reference.with_suffix(".info"))
        shutil.copyfile(example_dir + "md-02.en", changed.with_suffix(".en"))
        shutil.copyfile(example_dir + "md-02.info",
                        changed.with_suffix(".info"))

        reader = Reader(
            [
                str(reference.with_suffix(".en")),
                str(changed.with_suffix(".en")),
            ],
            MDEngineFormat.PQ,
        )

        changed_info = (changed.with_suffix(".info").read_text().replace(
            "A^3", "nm^3", 1))
        changed.with_suffix(".info").write_text(changed_info)

        with pytest.raises(ValueError, match="same units"):
            reader.read_last()
