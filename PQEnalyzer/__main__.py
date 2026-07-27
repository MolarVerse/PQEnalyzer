"""Command-line entry point for the GUI and TUI."""

import sys
import argparse

from . import __version__
from ._logging import configure_logging, get_logger


logger = get_logger(__name__)
APP_MODES = {"gui", "tui"}


def _argv_with_default_mode(argv):
    """
    Default bare file arguments to GUI mode.

    ``argparse`` subparsers normally treat the first positional argument as a
    required mode. For the common GUI path, allow users to omit that mode and
    pass files directly.
    """

    argv = list(argv)
    if not argv:
        return argv

    if argv[0] in {"-h", "--help", "-v", "--version", *APP_MODES}:
        return argv

    return ["gui", *argv]


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
                             help="Force QMCFC energy input.")
    input_group.add_argument("--box",
                             action="store_true",
                             help="Force PQ box input.")
    input_group.add_argument("--opt",
                             action="store_true",
                             help="Force PQ optimizer output format.")
    parser.add_argument(
        "filenames",
        metavar="FILE",
        nargs="+",
        help="Input file(s).")


def _input_format(args, parser):
    """
    Resolve explicit input-format arguments into a reader format.
    """

    forced_formats = [args.pq, args.qmcfc, args.box, args.opt]
    if sum(forced_formats) > 1:
        parser.error(
            "--pq, --qmcfc, --box, and --opt are mutually exclusive.")

    if args.pq:
        return "pq"
    if args.qmcfc:
        return "qmcfc"
    if args.box:
        return "box"
    if args.opt:
        return "opt"

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
        usage=(
            "%(prog)s [-h] [-v] [gui|tui] "
            "[--pq | -q | --box | --opt] FILE [FILE ...]"
        ),
        description="Plot and monitor PQ simulation output.",
        epilog="Pass files directly to open the GUI: pqenalyzer FILE [FILE ...]",
    )
    parser.add_argument("-v",
                        "--version",
                        action="version",
                        version=f"PQEnalyzer {__version__}")

    subparsers = parser.add_subparsers(
        dest="mode",
        metavar="[gui|tui]",
        required=True,
    )
    gui_parser = subparsers.add_parser("gui", help="Open the GUI (default).")
    _add_input_arguments(gui_parser)
    tui_parser = subparsers.add_parser(
        "tui",
        help="Open the terminal dashboard.",
    )
    _add_input_arguments(tui_parser)

    args = parser.parse_args(_argv_with_default_mode(sys.argv[1:]))
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
