"""
Reader selection for supported PQEnalyzer input formats.
"""

import contextlib
import io
import os
from pathlib import Path

from PQAnalysis.traj import MDEngineFormat

from .._logging import get_logger
from .box_reader import BoxReader
from .reader import Reader


AUTO_FORMAT = "auto"
PQ_FORMAT = "pq"
QMCFC_FORMAT = "qmcfc"
BOX_FORMAT = "box"
INPUT_FORMATS = {AUTO_FORMAT, PQ_FORMAT, QMCFC_FORMAT, BOX_FORMAT}

logger = get_logger(__name__)


class ReaderDetectionError(ValueError):
    """
    Raised when auto-detection cannot choose one reader unambiguously.
    """


def create_reader(filenames, input_format=AUTO_FORMAT):
    """
    Create a reader for the requested or auto-detected input format.
    """

    if input_format not in INPUT_FORMATS:
        raise ValueError(f"Unknown input format: {input_format}")

    filenames = list(filenames)

    if input_format == BOX_FORMAT:
        logger.info("Using box input.")
        return BoxReader(filenames)

    if input_format == PQ_FORMAT:
        logger.info("Using PQ energy input.")
        return Reader(filenames, MDEngineFormat.PQ)

    if input_format == QMCFC_FORMAT:
        logger.info("Using QMCFC energy input.")
        return Reader(filenames, MDEngineFormat.QMCFC)

    return _create_auto_reader(filenames)


def _create_auto_reader(filenames):
    """
    Select a reader by probing supported input formats.
    """

    if _contains_box_filename(filenames):
        if not _contains_only_box_filenames(filenames):
            raise ReaderDetectionError(
                "Cannot mix box files and energy files.")

        logger.info("Detected box input.")
        return BoxReader(filenames)

    pq_detected = _probe_energy_format(filenames, MDEngineFormat.PQ)
    qmcfc_detected = _probe_energy_format(filenames, MDEngineFormat.QMCFC)

    if pq_detected and not qmcfc_detected:
        logger.info("Detected PQ energy input.")
        return Reader(filenames, MDEngineFormat.PQ)

    if qmcfc_detected and not pq_detected:
        logger.info("Detected QMCFC energy input.")
        return Reader(filenames, MDEngineFormat.QMCFC)

    if pq_detected and qmcfc_detected:
        raise ReaderDetectionError(
            "Input files are ambiguous: both PQ and QMCFC readers accepted "
            "them. Use --pq or --qmcfc to force the energy format.")

    if not _all_files_exist(filenames):
        return Reader(filenames, MDEngineFormat.PQ)

    box_reader, _ = _probe_box_reader(filenames)
    if box_reader is not None:
        logger.info("Detected box input.")
        return box_reader

    return Reader(filenames, MDEngineFormat.PQ)


def _probe_energy_format(filenames, md_format):
    """
    Return whether all files can be read as one energy format.
    """

    return all(
        _detect_energy_format(filename) == md_format for filename in filenames)


def _detect_energy_format(filename):
    """
    Detect an energy file format from the matching PQAnalysis info file.
    """

    info_filename = os.path.splitext(str(filename))[0] + ".info"
    try:
        with open(info_filename, "r", encoding="utf-8") as info_file:
            info_rows = info_file.readlines()[3:-2]
    except OSError:
        return None

    if not info_rows:
        return None

    pq_format = True
    qmcfc_format = True

    for row in info_rows:
        columns = row.split()
        if len(columns) != 8:
            pq_format = False

        if len(columns) not in {6, 7}:
            qmcfc_format = False

    if pq_format and not qmcfc_format:
        return MDEngineFormat.PQ

    if qmcfc_format and not pq_format:
        return MDEngineFormat.QMCFC

    return None


def _probe_box_reader(filenames):
    """
    Try the box reader without leaking expected probe errors to the user.
    """

    with _suppress_probe_output():
        try:
            return BoxReader(filenames), None
        except Exception as error:  # pylint: disable=broad-exception-caught
            return None, error


@contextlib.contextmanager
def _suppress_probe_output():
    """
    Suppress noisy parse errors while auto-detection probes formats.
    """

    with contextlib.redirect_stdout(io.StringIO()):
        with contextlib.redirect_stderr(io.StringIO()):
            yield


def _contains_box_filename(filenames):
    """
    Return whether at least one filename looks like a box file.
    """

    return any(_is_box_filename(filename) for filename in filenames)


def _all_files_exist(filenames):
    """
    Return whether every input path exists.
    """

    return all(Path(filename).exists() for filename in filenames)


def _contains_only_box_filenames(filenames):
    """
    Return whether every filename looks like a box file.
    """

    return all(_is_box_filename(filename) for filename in filenames)


def _is_box_filename(filename):
    """
    Return whether a filename has the conventional box suffix.
    """

    return Path(filename).suffix.lower() == ".box"
