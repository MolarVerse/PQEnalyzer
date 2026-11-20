import pytest
from PQAnalysis.traj import MDEngineFormat

from PQEnalyzer.energy_access import (
    available_parameters,
    parameter_unit,
    parameter_values,
)
from PQEnalyzer.readers import Reader
from PQEnalyzer.readers.energy_header import (
    EnergyHeaderError,
    has_pq_header,
    read_pq_header,
)
from PQEnalyzer.readers.factory import create_reader


PQ_HEADER = (
    "# PQ energy file 1\n"
    "#STEP[-] SIMULATION-TIME[ps] TEMPERATURE[K] E(TOT)[kcal/mol]\n"
)
DATA = (
    "1 0.002 300.0 -10.5\n"
    "2 0.004 301.0 -10.7\n"
)


def write_energy(tmp_path, text, name="md.en"):
    energy_file = tmp_path / name
    energy_file.write_text(text)
    return str(energy_file)


def test_has_pq_header(tmp_path):
    assert has_pq_header(write_energy(tmp_path, PQ_HEADER + DATA))
    assert not has_pq_header(write_energy(tmp_path, DATA, "plain.en"))
    assert not has_pq_header(write_energy(tmp_path, "", "empty.en"))
    assert not has_pq_header(str(tmp_path / "missing.en"))


def test_read_pq_header_returns_names_and_units(tmp_path):
    info, units = read_pq_header(write_energy(tmp_path, PQ_HEADER + DATA))

    assert info == {
        "STEP": 0,
        "SIMULATION-TIME": 1,
        "TEMPERATURE": 2,
        "E(TOT)": 3,
    }
    assert units["STEP"] == "-"
    assert units["E(TOT)"] == "kcal/mol"


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (DATA, "does not start"),
        ("# PQ energy file 1\n", "does not start"),
        ("# PQ energy file 1\n1 0.002\n", "must list the columns"),
        ("# PQ energy file 1\n#STEP[-] TIME\n", "invalid header column"),
        ("# PQ energy file 1\n#STEP[-] STEP[-]\n", "duplicate"),
        ("# PQ energy file 1\n#\n", "no columns"),
    ],
)
def test_read_pq_header_rejects_malformed_headers(tmp_path, text, message):
    with pytest.raises(EnergyHeaderError, match=message):
        read_pq_header(write_energy(tmp_path, text))


def test_reader_takes_names_from_header_without_info_file(tmp_path):
    energy_file = write_energy(tmp_path, PQ_HEADER + DATA)

    energy = Reader([energy_file], MDEngineFormat.PQ).energies[0]

    assert available_parameters([energy]) == [
        "STEP",
        "SIMULATION-TIME",
        "TEMPERATURE",
        "E(TOT)",
    ]
    assert parameter_values(energy, "TEMPERATURE").tolist() == [300.0, 301.0]
    assert parameter_values(energy, "SIMULATION-TIME").tolist() == [
        0.002, 0.004
    ]
    assert parameter_unit(energy, "E(TOT)") == "kcal/mol"


def test_reader_prefers_info_file_over_header(tmp_path):
    energy_file = write_energy(tmp_path, PQ_HEADER + DATA)
    (tmp_path / "md.info").write_text(
        "-----\n"
        "| PQ info file |\n"
        "-----\n"
        "|   A   1 x   B   2 y |\n"
        "|   C   1 z   D   2 w |\n"
        "-----\n")

    energy = Reader([energy_file], MDEngineFormat.PQ).energies[0]

    assert list(energy.info) == ["A", "B", "C", "D"]


def test_reader_rejects_header_column_count_mismatch(tmp_path):
    energy_file = write_energy(tmp_path, PQ_HEADER + "1 0.002 300.0\n")

    with pytest.raises(EnergyHeaderError, match="lists 4 columns.*has 3"):
        Reader([energy_file], MDEngineFormat.PQ)


def test_reader_rejects_header_without_data(tmp_path):
    energy_file = write_energy(tmp_path, PQ_HEADER)

    with pytest.raises(EnergyHeaderError, match="has 0"):
        Reader([energy_file], MDEngineFormat.PQ)


def test_create_reader_detects_header_only_pq_file(tmp_path):
    energy_file = write_energy(tmp_path, PQ_HEADER + DATA)

    reader = create_reader([energy_file])

    assert reader.md_format == MDEngineFormat.PQ
    assert "E(TOT)" in reader.energies[0].info
