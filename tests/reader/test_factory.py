import pytest
from PQAnalysis.traj import MDEngineFormat

from PQEnalyzer.readers import factory
from PQEnalyzer.readers.factory import (
    BOX_FORMAT,
    PQ_FORMAT,
    QMCFC_FORMAT,
    ReaderDetectionError,
    create_reader,
)


class FakeReader:
    outcomes = {}
    calls = []

    def __init__(self, filenames, md_format):
        self.filenames = list(filenames)
        self.md_format = md_format
        self.calls.append((self.filenames, md_format))

        outcome = self.outcomes.get(md_format.value)
        if isinstance(outcome, Exception):
            print("probe stdout noise")
            raise outcome


class FakeBoxReader:
    error = None
    calls = []

    def __init__(self, filenames):
        self.filenames = list(filenames)
        self.calls.append(self.filenames)

        if self.error is not None:
            print("box stdout noise")
            raise self.error


@pytest.fixture(autouse=True)
def fake_readers(monkeypatch):
    FakeReader.outcomes = {}
    FakeReader.calls = []
    FakeBoxReader.error = None
    FakeBoxReader.calls = []

    monkeypatch.setattr(factory, "Reader", FakeReader)
    monkeypatch.setattr(factory, "BoxReader", FakeBoxReader)


def test_create_reader_rejects_unknown_input_format():
    with pytest.raises(ValueError, match="Unknown input format"):
        create_reader(["md.en"], input_format="xyz")


def test_create_reader_forces_box_format():
    reader = create_reader(["md.data"], input_format=BOX_FORMAT)

    assert isinstance(reader, FakeBoxReader)
    assert FakeBoxReader.calls == [["md.data"]]


def test_create_reader_forces_pq_format():
    reader = create_reader(["md.en"], input_format=PQ_FORMAT)

    assert isinstance(reader, FakeReader)
    assert reader.md_format == MDEngineFormat.PQ


def test_create_reader_forces_qmcfc_format():
    reader = create_reader(["md.en"], input_format=QMCFC_FORMAT)

    assert isinstance(reader, FakeReader)
    assert reader.md_format == MDEngineFormat.QMCFC


def test_auto_detects_box_suffix_case_insensitively():
    reader = create_reader(["run-a.BOX", "run-b.box"])

    assert isinstance(reader, FakeBoxReader)
    assert FakeBoxReader.calls == [["run-a.BOX", "run-b.box"]]
    assert FakeReader.calls == []


def test_auto_rejects_mixed_box_and_energy_filenames():
    with pytest.raises(ReaderDetectionError, match="Cannot mix box files"):
        create_reader(["run.box", "run.en"])

    assert FakeReader.calls == []
    assert FakeBoxReader.calls == []


def test_auto_detects_pq_when_only_pq_reader_accepts_input(monkeypatch):
    monkeypatch.setattr(
        factory,
        "_probe_energy_format",
        lambda filenames, md_format: md_format == MDEngineFormat.PQ,
    )

    reader = create_reader(["md.en"])

    assert isinstance(reader, FakeReader)
    assert reader.md_format == MDEngineFormat.PQ
    assert FakeReader.calls == [(["md.en"], MDEngineFormat.PQ)]


def test_auto_detects_qmcfc_when_only_qmcfc_reader_accepts_input(monkeypatch):
    monkeypatch.setattr(
        factory,
        "_probe_energy_format",
        lambda filenames, md_format: md_format == MDEngineFormat.QMCFC,
    )

    reader = create_reader(["md.en"])

    assert isinstance(reader, FakeReader)
    assert reader.md_format == MDEngineFormat.QMCFC


def test_auto_rejects_ambiguous_energy_input(monkeypatch):
    monkeypatch.setattr(factory, "_probe_energy_format",
                        lambda filenames, md_format: True)

    with pytest.raises(ReaderDetectionError, match="both PQ and QMCFC"):
        create_reader(["md.en"])


def test_auto_falls_back_to_box_probe_when_energy_detection_fails(monkeypatch,
                                                                  tmp_path):
    monkeypatch.setattr(factory, "_probe_energy_format",
                        lambda filenames, md_format: False)
    box_file = tmp_path / "box-without-extension.data"
    box_file.write_text("1 2 3 4 90 90 90\n")

    reader = create_reader([box_file])

    assert isinstance(reader, FakeBoxReader)


def test_auto_reruns_pq_reader_when_all_probes_fail(monkeypatch):
    monkeypatch.setattr(factory, "_probe_energy_format",
                        lambda filenames, md_format: False)
    FakeBoxReader.error = ValueError("not box")
    invalid = "examples/md-01.en"

    reader = create_reader([invalid])

    assert isinstance(reader, FakeReader)
    assert reader.md_format == MDEngineFormat.PQ


def test_auto_skips_box_probe_for_missing_files(monkeypatch):
    monkeypatch.setattr(factory, "_probe_energy_format",
                        lambda filenames, md_format: False)

    reader = create_reader(["missing.en"])

    assert isinstance(reader, FakeReader)
    assert reader.md_format == MDEngineFormat.PQ
    assert FakeBoxReader.calls == []


def test_probe_energy_format_detects_pq_info_file():
    assert factory._probe_energy_format(
        ["tests/data/md-01.en"],
        MDEngineFormat.PQ,
    ) is True
    assert factory._probe_energy_format(
        ["tests/data/md-01.en"],
        MDEngineFormat.QMCFC,
    ) is False


def test_probe_energy_format_detects_qmcfc_info_file(tmp_path):
    energy_file = tmp_path / "qmcfc.en"
    energy_file.write_text("1 2 3 4\n")
    energy_file.with_suffix(".info").write_text(
        "header\n"
        "header\n"
        "header\n"
        "| SIMULATION-TIME 1 TEMPERATURE 2 |\n"
        "| PRESSURE 1 E(TOT) 2 E(QM) |\n"
        "footer\n"
        "footer\n"
    )

    assert factory._probe_energy_format([energy_file],
                                        MDEngineFormat.QMCFC) is True
    assert factory._probe_energy_format([energy_file],
                                        MDEngineFormat.PQ) is False


def test_probe_energy_format_rejects_missing_or_invalid_info_file(tmp_path):
    missing = tmp_path / "missing.en"
    empty = tmp_path / "empty.en"
    invalid = tmp_path / "invalid.en"
    empty.write_text("1 2 3\n")
    empty.with_suffix(".info").write_text(
        "header\n"
        "header\n"
        "header\n"
        "footer\n"
        "footer\n"
    )
    invalid.write_text("1 2 3\n")
    invalid.with_suffix(".info").write_text(
        "header\n"
        "header\n"
        "header\n"
        "invalid row\n"
        "footer\n"
        "footer\n"
    )

    assert factory._probe_energy_format([missing], MDEngineFormat.PQ) is False
    assert factory._probe_energy_format([empty], MDEngineFormat.PQ) is False
    assert factory._probe_energy_format([invalid], MDEngineFormat.PQ) is False
