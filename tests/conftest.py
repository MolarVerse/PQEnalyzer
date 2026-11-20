import inspect
import logging
import shutil
from pathlib import Path

import matplotlib
import pytest
from PQAnalysis.io import EnergyFileReader


DATA = Path(__file__).resolve().parent / "data"

# PQAnalysis >= 1.9 reports steps for PQ files without timestep metadata.
UNTIMED_PQ_TIME_UNIT = ("step" if "timestep_fs" in inspect.signature(
    EnergyFileReader).parameters else "ps")


matplotlib.use("Agg")


@pytest.fixture(name="untimed_time_unit")
def untimed_time_unit_fixture():
    """Return the time unit the installed PQAnalysis gives untimed PQ files."""
    return UNTIMED_PQ_TIME_UNIT


@pytest.fixture(name="timed_md_files")
def timed_md_files_fixture(tmp_path):
    """Copy md-01/md-02 with a 1000 fs timestep, so one step is one ps."""
    filenames = []
    for stem in ("md-01", "md-02"):
        shutil.copy(DATA / f"{stem}.info", tmp_path / f"{stem}.info")
        energy_file = tmp_path / f"{stem}.en"
        energy_file.write_text("# timestep = 1000 fs\n" +
                               (DATA / f"{stem}.en").read_text(
                                   encoding="utf-8"),
                               encoding="utf-8")
        filenames.append(str(energy_file))
    return filenames


@pytest.fixture(name="terminal_log")
def terminal_log_fixture(caplog):
    """Capture records from the independent application event logger."""
    from PQEnalyzer._terminal import event_logger

    previous_level = event_logger.level
    event_logger.setLevel(logging.DEBUG)
    event_logger.addHandler(caplog.handler)
    caplog.clear()
    try:
        yield caplog
    finally:
        event_logger.removeHandler(caplog.handler)
        event_logger.setLevel(previous_level)
