"""Command-line entry point for the web and desktop interfaces."""

import logging
import sys

from . import __version__
from ._logging import configure_logging
from ._terminal import event_logger, print_desktop_startup, terminal


APP_MODES = {"gui", "web"}
LOG_LEVELS = ("debug", "info", "warning", "error")


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
    Add shared input arguments for web and GUI modes.
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


def _add_log_level_argument(parser):
    """Add the shared application-event verbosity control."""
    parser.add_argument(
        "--log-level",
        choices=LOG_LEVELS,
        default="info",
        help="Event detail (default: %(default)s).",
    )


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
    parser = terminal.argument_parser(
        prog="pqenalyzer",
        description="Plot and monitor PQ simulation output.",
        epilog=(
            "Pass files directly to open the desktop GUI: "
            "pqenalyzer FILE [FILE ...]"
        ),
    )
    parser.add_argument("-v",
                        "--version",
                        action="version",
                        version=f"PQEnalyzer {__version__}")

    subparsers = parser.add_subparsers(
        dest="mode",
        metavar="[gui|web]",
        required=True,
    )
    gui_parser = subparsers.add_parser(
        "gui",
        help="Open the desktop GUI (default).",
    )
    _add_input_arguments(gui_parser)
    _add_log_level_argument(gui_parser)
    web_parser = subparsers.add_parser(
        "web",
        help="Open the browser UI.",
    )
    _add_input_arguments(web_parser)
    web_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host (loopback only; default: %(default)s).",
    )
    web_parser.add_argument(
        "--port",
        type=int,
        default=8766,
        help="Server port (default: %(default)s).",
    )
    web_parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open a browser.",
    )
    _add_log_level_argument(web_parser)

    args = parser.parse_args(_argv_with_default_mode(sys.argv[1:]))
    # Keep PQAnalysis and application internals quiet at their INFO level;
    # the independent terminal logger owns concise CLI events for both modes.
    configure_logging(logging.WARNING)
    terminal.configure_logging(args.log_level)

    from .readers import create_reader

    try:
        reader = create_reader(
            args.filenames,
            input_format=_input_format(args, parser),
        )
    except Exception as e:
        if not e.__class__.__module__.startswith("PQAnalysis"):
            event_logger.error("%s", e)
        sys.exit(1)

    if args.mode == "web":
        # The reader was validated above.
        from .web import serve

        if not 1 <= args.port <= 65535:
            parser.error("--port must be between 1 and 65535.")
        if args.host not in ("127.0.0.1", "localhost", "::1"):
            parser.error("--host must be a loopback address (127.0.0.1, localhost or ::1).")
        try:
            serve(
                args.filenames,
                _input_format(args, parser),
                host=args.host,
                port=args.port,
                open_browser=not args.no_open,
                reader=reader,
                log_level=args.log_level,
            )
        except ValueError as error:
            parser.error(str(error))
        except KeyboardInterrupt:
            raise SystemExit(130) from None
    else:
        from .apps import App

        app = App(reader)
        app.build()
        app.update_idletasks()
        print_desktop_startup(reader)
        event_logger.info("Desktop ready.")
        app.mainloop()
        event_logger.info("Desktop closed.")

    return None


if __name__ == "__main__":
    main()
