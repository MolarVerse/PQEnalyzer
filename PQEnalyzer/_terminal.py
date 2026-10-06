"""PQEnalyzer terminal identity and browser-server messages."""

from . import __version__
from ._design_terminal import Terminal
from .flat_mono import COLORS


terminal = Terminal("PQEnalyzer", __version__, COLORS)
event_logger = terminal.log


def data_summary(row_count, file_count):
    """Return a compact dataset size for startup and refresh events."""
    rows_label = "row" if row_count == 1 else "rows"
    files_label = "file" if file_count == 1 else "files"
    return f"{row_count:,} {rows_label} / {file_count} {files_label}"


def print_web_startup(url, row_count, file_count):
    """Present a ready browser server with its current dataset size."""
    terminal.startup(
        url,
        details=(("Data", data_summary(row_count, file_count)),),
    )


def print_desktop_startup(reader):
    """Present a built desktop window with its current dataset size."""
    row_count = sum(len(energy.simulation_time) for energy in reader.energies)
    terminal.desktop(
        details=((
            "Data",
            data_summary(row_count, len(reader.filenames)),
        ),),
    )
