from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PQAnalysis.io.exceptions import OptimizerReaderError

from PQEnalyzer.readers import OptimizerReader


OPTIMIZER_PARAMETERS = [
    "SIMULATION-TIME",
    "ABS-ENERGY-CHANGE",
    "REL-ENERGY-CHANGE",
    "MAX-FORCE",
    "RMS-FORCE",
    "REL-ENERGY-CONV",
    "ABS-ENERGY-CONV",
    "MAX-FORCE-CONV",
    "RMS-FORCE-CONV",
    "REL-ENERGY-LIMIT",
    "ABS-ENERGY-LIMIT",
    "MAX-FORCE-LIMIT",
    "RMS-FORCE-LIMIT",
]


def test_optimizer_reader_exposes_real_pq_output_schema():
    reader = OptimizerReader(["examples/optimization.opt"])

    assert reader.filenames == ["examples/optimization.opt"]
    assert len(reader.energies) == 1

    energy = reader.energies[0]
    assert list(energy.info) == OPTIMIZER_PARAMETERS
    assert energy.units["MAX-FORCE"] == "kcal/mol/A"
    assert energy.units["REL-ENERGY-CONV"] == "state"
    assert energy.axis_label == "Optimization Step"
    assert energy.data.shape == (len(OPTIMIZER_PARAMETERS), 11)
    np.testing.assert_array_equal(energy.simulation_time, np.arange(1, 12))
    assert energy.data[energy.info["ABS-ENERGY-CHANGE"]][-1] == pytest.approx(
        388.243509)
    assert energy.data[energy.info["RMS-FORCE"]][-1] == pytest.approx(
        24.8886764)
    np.testing.assert_array_equal(
        energy.data[energy.info["REL-ENERGY-CONV"]],
        np.array([1, *([-1] * 10)]),
    )


def test_optimizer_reader_supports_multiple_files_and_live_refresh(tmp_path):
    first = tmp_path / "first.opt"
    growing = tmp_path / "growing.opt"
    source_data = Path("examples/optimization.opt").read_text(encoding="utf-8")
    first.write_text(source_data, encoding="utf-8")
    growing.write_text(source_data, encoding="utf-8")

    reader = OptimizerReader([first, growing])
    original_first = reader.energies[0]
    original_last = reader.energies[-1]

    with growing.open("a", encoding="utf-8") as output_file:
        output_file.write(
            "12 3.0e+02 2.0e-02 1.2e+02 2.0e+01 "
            "-1 -1 -1 -1 1e-14 1e-14 1e-14 1e-14\n")

    reader.read_last()

    assert reader.energies[0] is original_first
    assert reader.energies[-1] is not original_last
    assert len(reader.energies[-1].simulation_time) == 12
    assert reader.energies[-1].simulation_time[-1] == 12


def test_optimizer_reader_rejects_empty_filename_list():
    with pytest.raises(ValueError, match="list of filenames is empty"):
        OptimizerReader([])


def test_optimizer_reader_rejects_empty_file(tmp_path):
    filename = tmp_path / "empty.opt"
    filename.write_text("", encoding="utf-8")

    with pytest.raises(OptimizerReaderError,
                       match="does not contain optimizer data"):
        OptimizerReader([filename])


def test_optimizer_reader_rejects_wrong_column_count(tmp_path):
    filename = tmp_path / "invalid.opt"
    filename.write_text("1 2 3 4\n", encoding="utf-8")

    with pytest.raises(OptimizerReaderError, match="Expected 13 columns"):
        OptimizerReader([filename])


def test_optimizer_reader_rejects_inconsistent_rows(tmp_path):
    filename = tmp_path / "inconsistent.opt"
    filename.write_text(
        "1 2 3 4 5 6 7 8 9 10 11 12 13\n"
        "2 3 4\n",
        encoding="utf-8",
    )

    with pytest.raises(OptimizerReaderError, match="Expected 13 columns"):
        OptimizerReader([filename])


def test_optimizer_reader_delegates_single_file_parsing_to_pqanalysis(
        monkeypatch):
    calls = []
    parsed_energy = SimpleNamespace()

    def fake_read_optimizer_file(filename):
        calls.append(filename)
        return parsed_energy

    monkeypatch.setattr(
        "PQEnalyzer.readers.optimizer_reader.read_optimizer_file",
        fake_read_optimizer_file,
    )

    energy = OptimizerReader._read_optimizer_file("run.opt")

    assert calls == ["run.opt"]
    assert energy is parsed_energy
    assert energy.axis_label == "Optimization Step"
