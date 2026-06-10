"""
Command-line entrypoint for PQEnalyzer.

The CLI reads one or more data files through a PQAnalysis-backed reader and
then starts either the graphical CustomTkinter application or the terminal
plotting flow. GUI imports stay inside main() so terminal mode can start
without loading Tkinter.
"""

import sys
import argparse
import argcomplete

from . import __version__
from ._logging import configure_logging, get_logger


logger = get_logger(__name__)


def main():
    """
    Parse command-line arguments, read input files, and start the chosen UI.

    PQAnalysis exceptions are allowed to keep their own formatting. Other
    reader errors are logged through the application logger before returning a
    non-zero process exit.
    """
    parser = argparse.ArgumentParser(description="PQEnalyzer - MolarVerse")
    parser.add_argument(
        "filenames",
        metavar="filenames",
        nargs="+",
        help="The name of the energy files to read the data from.")
    parser.add_argument("-q",
                        "--qmcfc",
                        action="store_true",
                        help="Use the QMCFC output as input.")
    parser.add_argument("--box",
                        action="store_true",
                        help="Read PQ box files instead of energy files.")
    parser.add_argument("-n",
                        "--no-gui",
                        action="store_true",
                        help="Opens the terminal plotting feature.")
    parser.add_argument("-v",
                        "--version",
                        action="version",
                        version=f"PQEnalyzer {__version__}")

    argcomplete.autocomplete(parser)

    args = parser.parse_args()
    configure_logging()

    from PQAnalysis.traj import MDEngineFormat

    from .readers import BoxReader, Reader

    md_format = MDEngineFormat.PQ

    if args.box and args.qmcfc:
        parser.error("--box cannot be combined with --qmcfc.")

    if args.qmcfc:
        md_format = MDEngineFormat.QMCFC

    try:
        if args.box:
            reader = BoxReader(args.filenames)
        else:
            reader = Reader(args.filenames, md_format)
    except Exception as e:
        if not e.__class__.__module__.startswith("PQAnalysis"):
            logger.error("%s", e)
        sys.exit(1)

    if args.no_gui:
        from .apps import TermApp

        termapp = TermApp(reader)
        termapp.start()
    else:
        from .apps import App

        app = App(reader)
        app.build()
        app.mainloop()

    return None


if __name__ == "__main__":
    main()
