"""
Application entrypoint for PQEnalyzer.

The entrypoint reads one or more data files through a PQAnalysis-backed reader
and then starts the graphical CustomTkinter application or the terminal
dashboard. GUI imports stay inside main() so terminal mode can start without
loading Tkinter.
"""

import sys
import argparse

from . import __version__
from ._logging import configure_logging, get_logger


logger = get_logger(__name__)


def _add_input_arguments(parser):
    """
    Add shared input arguments for GUI and TUI modes.
    """

    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--pq",
                             action="store_true",
                             help="Force PQ energy input.")
    input_group.add_argument("-q",
                             "--qmcfc",
                             action="store_true",
                             help="Use the QMCFC output as input.")
    input_group.add_argument("--box",
                             action="store_true",
                             help="Read PQ box files instead of energy files.")
    parser.add_argument(
        "filenames",
        metavar="filenames",
        nargs="+",
        help="The name of the files to read the data from.")


def _input_format(args, parser):
    """
    Resolve explicit input-format arguments into a reader format.
    """

    forced_formats = [args.pq, args.qmcfc, args.box]
    if sum(forced_formats) > 1:
        parser.error("--pq, --qmcfc, and --box are mutually exclusive.")

    if args.pq:
        return "pq"
    if args.qmcfc:
        return "qmcfc"
    if args.box:
        return "box"

    return "auto"


def main():
    """
    Parse command-line arguments, read input files, and start the chosen UI.

    PQAnalysis exceptions are allowed to keep their own formatting. Other
    reader errors are logged through the application logger before returning a
    non-zero process exit.
    """
    parser = argparse.ArgumentParser(
        prog="pqenalyzer",
        description="PQEnalyzer - MolarVerse",
    )
    parser.add_argument("-v",
                        "--version",
                        action="version",
                        version=f"PQEnalyzer {__version__}")

    subparsers = parser.add_subparsers(
        dest="mode",
        metavar="{gui,tui}",
        required=True,
    )
    gui_parser = subparsers.add_parser("gui", help="Open the graphical app.")
    _add_input_arguments(gui_parser)
    tui_parser = subparsers.add_parser(
        "tui",
        help="Open the terminal dashboard.",
    )
    _add_input_arguments(tui_parser)

    args = parser.parse_args()
    configure_logging()

    from .readers import create_reader

    try:
        reader = create_reader(
            args.filenames,
            input_format=_input_format(args, parser),
        )
    except Exception as e:
        if not e.__class__.__module__.startswith("PQAnalysis"):
            logger.error("%s", e)
        sys.exit(1)

    if args.mode == "tui":
        from .apps import TuiApp

        TuiApp(reader).run()
    else:
        from .apps import App

        app = App(reader)
        app.build()
        app.mainloop()

    return None


if __name__ == "__main__":
    main()
